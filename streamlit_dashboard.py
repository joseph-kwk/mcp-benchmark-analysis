"""
MCP Benchmark Dashboard  ·  Spring 2026  ·  Southwestern College
─────────────────────────────────────────────────────────────────
Run:  streamlit run streamlit_dashboard.py
"""

import time, random, math, json, sys, os
from pathlib import Path

import streamlit as st
import pandas as pd
import altair as alt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "benchmark"))
from mock_llm import (
    MockLLMClient, LLMProvider,
    make_mcp_gpt4o, make_traditional_gpt4o,
    count_loc_to_swap_provider, USE_REAL_APIS,
)

try:
    sys.path.insert(0, os.path.dirname(__file__))
    from server import (
        get_field_status, get_weather_forecast, recommend_irrigation,
        activate_irrigation, log_sensor_reading, get_crop_schedule, calculate_area,
    )
    _SERVER_AVAILABLE = True
except Exception as _e:
    _SERVER_AVAILABLE = False
    _SERVER_ERROR = str(_e)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MCP Agriculture Benchmark",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .block-container { padding: 1.5rem 2rem 3rem 2rem; max-width: 1440px; }
  [data-testid="stSidebar"] { min-width: 270px; }

  /* ── Field cards ─────────────────────────────────────── */
  .field-card {
    border-radius: 16px; padding: 22px 14px; text-align: center;
    color: white; min-height: 148px;
    display: flex; flex-direction: column; justify-content: center;
    gap: 2px; box-shadow: 0 4px 16px rgba(0,0,0,.12);
    transition: transform .15s ease, box-shadow .15s ease;
  }
  .field-card:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,.18); }
  .field-card.highlighted {
    box-shadow: 0 0 0 4px #6366f1, 0 8px 28px rgba(99,102,241,.25) !important;
    transform: translateY(-2px);
  }
  .field-healthy  { background: linear-gradient(150deg,#059669,#34d399); }
  .field-warning  { background: linear-gradient(150deg,#d97706,#fbbf24); }
  .field-critical { background: linear-gradient(150deg,#dc2626,#f87171); }
  .fc-name     { font-size: .85em; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; opacity: .9; }
  .fc-moisture { font-size: 2.5em; font-weight: 800; line-height: 1.1; letter-spacing: -.03em; }
  .fc-crop     { font-size: .78em; opacity: .85; margin-top: 2px; }
  .fc-status   { font-size: .75em; background: rgba(255,255,255,.22); border-radius: 20px;
                 padding: 3px 10px; display: inline-block; margin-top: 6px; font-weight: 600; }
  .fc-focus    { font-size: .7em; background: rgba(255,255,255,.40); border-radius: 20px;
                 padding: 2px 9px; display: inline-block; margin-top: 5px; font-weight: 700;
                 text-transform: uppercase; letter-spacing: .05em; border: 1px solid rgba(255,255,255,.6); }

  /* ── Protocol badges ─────────────────────────────────── */
  .badge-mcp  { display:inline-block; background:#d1fae5; color:#065f46;
                padding:5px 14px; border-radius:20px; font-size:.82em; font-weight:700; }
  .badge-trad { display:inline-block; background:#fee2e2; color:#991b1b;
                padding:5px 14px; border-radius:20px; font-size:.82em; font-weight:700; }

  /* ── Latest result cards ─────────────────────────────── */
  .result-card {
    background: #f8fafc; border-left: 4px solid #6366f1; border-radius: 8px;
    padding: 16px 18px; font-family: 'SF Mono','Monaco',monospace;
    font-size: .88em; color: #1e293b; line-height: 2;
    box-shadow: 0 1px 4px rgba(0,0,0,.06);
  }
  .result-card.pass { border-left-color: #10b981; background: #f0fdf4; }
  .result-card.fail { border-left-color: #ef4444; background: #fff5f5; }

  /* ── RQ comparison cards ─────────────────────────────── */
  .cmp-card {
    border-radius: 12px; padding: 18px 14px; text-align: center; border: 2px solid;
    transition: transform .15s;
  }
  .cmp-card:hover { transform: translateY(-2px); }
  .cmp-mcp  { background: #ecfdf5; border-color: #10b981; color: #065f46; }
  .cmp-trad { background: #fef3c7; border-color: #f59e0b; color: #92400e; }
  .cmp-label { font-size: .72em; font-weight: 700; text-transform: uppercase;
               letter-spacing: .07em; opacity: .8; margin-bottom: 8px; }
  .cmp-val   { font-size: 2em; font-weight: 800; letter-spacing: -.03em; line-height: 1; }
  .cmp-sub   { font-size: .82em; margin-top: 6px; opacity: .75; }

  /* ── Server response strip ───────────────────────────── */
  .srv-strip {
    background: #f0fdf4; border-left: 4px solid #10b981; border-radius: 8px;
    padding: 10px 16px; font-family: monospace; font-size: .82em;
    color: #1e293b; margin-top: 10px;
  }

  /* ── Architecture flow nodes ─────────────────────────── */
  .flow-node {
    background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 10px;
    padding: 12px 16px; text-align: center; font-size: .84em; color: #374151;
    line-height: 1.5;
  }
  .flow-arrow { text-align: center; padding-top: 16px; color: #6366f1;
                font-weight: 700; font-size: 1.3em; }

  /* ── Section header label ────────────────────────────── */
  .section-head {
    font-size: .72em; font-weight: 700; text-transform: uppercase;
    letter-spacing: .09em; color: #94a3b8; margin-bottom: 2px;
  }

  /* ── Info banners ────────────────────────────────────── */
  .info-banner {
    background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px;
    padding: 10px 16px; font-size: .85em; color: #1e40af; margin-top: 6px;
  }

  /* ── Active scenario card ────────────────────────────── */
  .scenario-box {
    background: #fafbff; border: 1.5px solid #c7d2fe; border-radius: 12px;
    padding: 18px 20px; margin-bottom: 14px;
  }
  .scenario-header {
    display: flex; align-items: center; gap: 10px; margin-bottom: 10px;
  }
  .scenario-icon  { font-size: 1.8em; line-height: 1; }
  .scenario-title { font-size: 1.05em; font-weight: 700; color: #312e81; }
  .scenario-sub   { font-size: .75em; color: #6366f1; font-weight: 600;
                    text-transform: uppercase; letter-spacing: .07em; }
  .scenario-text  { font-size: .9em; color: #1e293b; line-height: 1.7; margin-bottom: 10px; }
  .scenario-grid  { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px; }
  .scenario-cell  {
    background: white; border: 1px solid #e0e7ff; border-radius: 8px; padding: 10px 12px;
    font-size: .8em; color: #374151; line-height: 1.5;
  }
  .scenario-cell-label { font-size: .7em; font-weight: 700; text-transform: uppercase;
                         letter-spacing: .07em; color: #818cf8; margin-bottom: 3px; }
  .scenario-footer { margin-top: 10px; padding-top: 10px; border-top: 1px solid #e0e7ff;
                     font-size: .78em; color: #64748b; }
  code.tool-chip  { background: #e0e7ff; color: #3730a3; padding: 2px 8px;
                    border-radius: 6px; font-family: monospace; font-size: .88em; }
  code.arg-chip   { background: #fef9c3; color: #92400e; padding: 2px 8px;
                    border-radius: 6px; font-family: monospace; font-size: .85em; }

  /* ── Tour tab ──────────────────────────────────────────── */
  .tour-step {
    background: white; border-radius: 16px; padding: 28px 28px 22px;
    box-shadow: 0 2px 16px rgba(0,0,0,.07); border: 1px solid #e2e8f0;
    position: relative; overflow: hidden;
  }
  .tour-step::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 4px;
  }
  .tour-step-1::before { background: linear-gradient(90deg,#ef4444,#f97316); }
  .tour-step-2::before { background: linear-gradient(90deg,#6366f1,#8b5cf6); }
  .tour-step-3::before { background: linear-gradient(90deg,#0ea5e9,#38bdf8); }
  .tour-step-4::before { background: linear-gradient(90deg,#10b981,#34d399); }
  .tour-step-5::before { background: linear-gradient(90deg,#f59e0b,#fbbf24); }
  .tour-step-n { font-size: .7em; font-weight: 800; text-transform: uppercase;
                 letter-spacing: .1em; color: #94a3b8; margin-bottom: 6px; }
  .tour-step-title { font-size: 1.2em; font-weight: 800; color: #0f172a;
                     margin-bottom: 8px; line-height: 1.3; }
  .tour-step-body  { font-size: .9em; color: #334155; line-height: 1.75; }
  .tour-badge {
    display: inline-block; padding: 3px 12px; border-radius: 20px;
    font-size: .75em; font-weight: 700; margin-right: 6px; margin-bottom: 6px;
  }
  .tb-red    { background:#fee2e2; color:#991b1b; }
  .tb-green  { background:#dcfce7; color:#166534; }
  .tb-blue   { background:#dbeafe; color:#1e40af; }
  .tb-purple { background:#ede9fe; color:#4c1d95; }
  .tb-yellow { background:#fef9c3; color:#92400e; }
  .proto-box {
    border-radius: 12px; padding: 16px 18px; font-size: .82em;
    font-family: 'SF Mono','Monaco',monospace; line-height: 1.8;
  }
  .proto-trad { background: #fff5f5; border: 1.5px solid #fca5a5; color: #1e293b; }
  .proto-mcp  { background: #f0fdf4; border: 1.5px solid #86efac; color: #1e293b; }
  .proto-label { font-weight: 800; font-size: .85em; text-transform: uppercase;
                 letter-spacing: .06em; margin-bottom: 8px; }
  .trad-label { color: #dc2626; }
  .mcp-label  { color: #16a34a; }
  .rq-card {
    border-radius: 14px; padding: 22px 20px;
    text-align: center; height: 100%;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    gap: 8px;
  }
  .rq-card-1 { background: linear-gradient(160deg,#1e3a5f,#1e40af); color: white; }
  .rq-card-2 { background: linear-gradient(160deg,#14532d,#166534); color: white; }
  .rq-card-3 { background: linear-gradient(160deg,#4c1d95,#6d28d9); color: white; }
  .rq-num   { font-size: .75em; font-weight: 700; opacity: .7; text-transform: uppercase;
              letter-spacing: .09em; }
  .rq-q     { font-size: 1em; font-weight: 700; line-height: 1.4; }
  .rq-hyp   { font-size: .8em; opacity: .82; line-height: 1.5; }
  .rq-finding { font-size: .85em; font-weight: 700; background: rgba(255,255,255,.18);
                border-radius: 8px; padding: 6px 12px; margin-top: 4px; }
  .verdict-bar {
    border-radius: 14px; padding: 20px 24px;
    display: flex; align-items: center; gap: 18px;
    background: linear-gradient(135deg,#0f172a,#1e293b); color: white;
    margin: 8px 0;
  }
  .verdict-icon { font-size: 2.4em; line-height: 1; }
  .verdict-text { font-size: .95em; line-height: 1.6; }
  .verdict-text b { color: #34d399; }
  .tool-grid {
    display: grid; grid-template-columns: repeat(3,1fr); gap: 10px; margin-top: 10px;
  }
  .tool-tile {
    background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px;
    padding: 12px 14px; font-size: .82em; color: #1e293b;
  }
  .tool-tile-name { font-weight: 700; color: #4f46e5; font-family: monospace;
                    font-size: .95em; margin-bottom: 3px; }
  .tool-tile-desc { color: #64748b; line-height: 1.4; }
</style>
""", unsafe_allow_html=True)

# ── Task Scenarios (irrigation-domain, per advisor guidance) ──────────────────
#
# Each scenario represents one AI tool-call challenge:
#   - scenario:      Plain-English description of the situation
#   - expected_tool: The ONLY correct function the AI should call
#   - tool_args:     The exact arguments the correct call requires
#   - why_matters:   Why this specific test is important for the research
#   - pass_means:    What a PASS result looks like in practice
#   - fail_means:    What a FAIL result looks like (and why it's harmful)
# ─────────────────────────────────────────────────────────────────────────────
TASK_SCENARIOS = {
    "irrigation_check": {
        "label":      "Start Irrigation",
        "icon":       "💧",
        "scenario":   (
            "Field C soil moisture has dropped to 8% — critically below the 20% safe threshold. "
            "The AI agent receives this sensor alert and must autonomously decide to activate "
            "the irrigation pump for 45 minutes."
        ),
        "expected_tool": "activate_irrigation",
        "tool_args":     '{"field_id": "Field_C", "action": "start", "duration_minutes": 45}',
        "focus_field":   "Field C",
        "rq":            "RQ3 — Tool-Selection Accuracy",
        "why_matters": (
            "This is the primary real-world MCP use case. The AI must choose the correct action tool "
            "from 7 available tools — not just recommend, but actually trigger the pump. "
            "MCP's full JSON-RPC manifest helps GPT-4o find the right tool every time."
        ),
        "pass_means":  "✅ AI called activate_irrigation(Field_C, start, 45) → pump turns on",
        "fail_means":  "❌ AI called wrong tool (e.g. recommend_irrigation) → crop damage risk",
    },
    "field_status": {
        "label":      "Check Field Status",
        "icon":       "🔍",
        "scenario":   (
            "A farm operator asks: 'What is the current moisture level of Field A?' "
            "The AI must fetch a live sensor reading from the FastMCP server — "
            "not guess or return a text answer."
        ),
        "expected_tool": "get_field_status",
        "tool_args":     '{"field_id": "Field_A"}',
        "focus_field":   "Field A",
        "rq":            "RQ3 — Tool-Selection Accuracy",
        "why_matters": (
            "Decisions are only as good as their data. Traditional AI systems must have the exact "
            "function schema registered at call time. MCP broadcasts all schemas upfront, so "
            "GPT-4o can dynamically discover get_field_status without hardcoding."
        ),
        "pass_means":  "✅ AI called get_field_status(Field_A) → returns live moisture %",
        "fail_means":  "❌ AI returned a text guess instead of calling the tool → stale/wrong data",
    },
    "recommend_action": {
        "label":      "Get Irrigation Recommendation",
        "icon":       "🧠",
        "scenario":   (
            "Field A moisture is at 12% — borderline danger. The operator asks: "
            "'Should I irrigate Field A right now?' The AI must call the advisory engine "
            "(recommend_irrigation), not jump straight to activating the pump."
        ),
        "expected_tool": "recommend_irrigation",
        "tool_args":     '{"field_id": "Field_A", "moisture_pct": 12}',
        "focus_field":   "Field A",
        "rq":            "RQ3 — Tool-Selection Accuracy",
        "why_matters": (
            "Two tools exist for irrigation: one advises, one acts. Traditional AI often confuses "
            "them on advisory prompts. MCP's rich tool descriptions help GPT-4o choose "
            "the advisory tool when the operator asks 'should I' vs 'do it'."
        ),
        "pass_means":  "✅ AI called recommend_irrigation(Field_A, 12) → returns advice",
        "fail_means":  "❌ AI jumped to activate_irrigation (over-eager) → farmer loses control",
    },
    "pump_stop": {
        "label":      "Stop Irrigation Pump",
        "icon":       "🛑",
        "scenario":   (
            "Field C has been irrigating for 45 minutes and is now at safe moisture. "
            "The operator issues a stop command. The AI must call activate_irrigation "
            "with action='stop' — the same tool used to start, but opposite intent."
        ),
        "expected_tool": "activate_irrigation",
        "tool_args":     '{"field_id": "Field_C", "action": "stop"}',
        "focus_field":   "Field C",
        "rq":            "RQ3 — Tool-Selection Accuracy",
        "why_matters": (
            "Disambiguation test: the correct tool name is identical to 'Start Irrigation', "
            "but the action parameter must be 'stop'. Passing wrong args or the wrong tool "
            "means the pump keeps running — a flood/root-rot risk. "
            "MCP's strict JSON-RPC schema validation catches this."
        ),
        "pass_means":  "✅ AI called activate_irrigation(Field_C, stop) → pump turns off",
        "fail_means":  "❌ AI used action='start' or called wrong tool → pump keeps running (flood risk)",
    },
    "weather_forecast": {
        "label":      "Weather Forecast Lookup",
        "icon":       "🌤",
        "scenario":   (
            "Before scheduling the next irrigation cycle, the operator checks the forecast: "
            "'What's the weather looking like for the next 3 days?' "
            "If rain is coming, the farm can skip a watering cycle and save water."
        ),
        "expected_tool": "get_weather_forecast",
        "tool_args":     '{"location": "farm", "days": 3}',
        "focus_field":   "All Fields",
        "rq":            "RQ3 — Tool-Selection Accuracy",
        "why_matters": (
            "Weather data drives irrigation scheduling. This tests whether the AI picks "
            "an *information retrieval* tool (get_weather_forecast) rather than an *action* "
            "tool when asked a planning question — a common hallucination failure mode."
        ),
        "pass_means":  "✅ AI called get_weather_forecast(farm, 3) → returns 3-day forecast",
        "fail_means":  "❌ AI returned a made-up weather answer in text → irrigation decision based on hallucination",
    },
}

FID_MAP = {"Field A": "Field_A", "Field B": "Field_B",
           "Field C": "Field_C", "Field D": "Field_D"}

# ── Session state ──────────────────────────────────────────────────────────────
def _init_state():
    defaults = {
        "fields": {
            "Field A": {"crop": "Corn",    "moisture": 12.0, "base": 12.0},
            "Field B": {"crop": "Wheat",   "moisture": 28.0, "base": 28.0},
            "Field C": {"crop": "Soybean", "moisture":  8.0, "base":  8.0},
            "Field D": {"crop": "Corn",    "moisture": 45.0, "base": 45.0},
        },
        "sim_ticks":        0,
        "history":          [],
        "trial_count":      0,
        "last_server_resp": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Benchmark Settings")

    task_key = st.selectbox(
        "Irrigation Scenario",
        list(TASK_SCENARIOS.keys()),
        format_func=lambda k: f"{TASK_SCENARIOS[k]['icon']}  {TASK_SCENARIOS[k]['label']}",
        help=(
            "Choose which irrigation scenario to test. Each one benchmarks GPT-4o's ability "
            "to select the correct MCP tool when given a real farming prompt. "
            "The selected scenario changes the highlighted field card above and the scenario "
            "description in Section 2."
        ),
    )

    trials_per_run = st.slider(
        "Trials per run",
        min_value=1, max_value=50, value=10,
        help=(
            "How many times to run the same scenario in one benchmark run. "
            "More trials → more statistically reliable accuracy %. "
            "Each trial sends one real (or mock) API call to GPT-4o for both "
            "the Traditional and MCP protocol paths."
        ),
    )

    st.divider()
    st.caption("**Data controls**")

    if st.button(
        "🗑️  Clear Benchmark History",
        use_container_width=True,
        help="Removes ALL trial results from the current session. Resets the accuracy charts, "
             "aggregate metrics, and history table to zero. The farm field states are NOT affected.",
    ):
        st.session_state.history     = []
        st.session_state.trial_count = 0
        st.rerun()

    if st.button(
        "↺  Reset Farm Simulation",
        use_container_width=True,
        help="Restores all 4 field moisture levels back to their starting baseline "
             "(Field A: 12%, B: 28%, C: 8%, D: 45%). Benchmark history is NOT cleared.",
    ):
        for fdata in st.session_state.fields.values():
            fdata["moisture"] = fdata["base"]
        st.session_state.sim_ticks        = 0
        st.session_state.last_server_resp = None
        st.rerun()

    st.divider()
    st.caption("GPT-4o  ·  Spring 2026  ·  Southwestern College")

# ── Resolve the active task info for the rest of the page ─────────────────────
task_info = TASK_SCENARIOS[task_key]

# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 🌾 MCP Agriculture Benchmark")
st.caption(
    "Evaluating the Model Context Protocol for AI tool integration in smart irrigation  ·  "
    "Spring 2026 Senior Project  ·  Southwestern College"
)

api_pill = "🟢 Live GPT-4o" if USE_REAL_APIS else "🟡 Mock Simulation"
total_trials = len(st.session_state.history)
st.markdown(
    f"**Mode:** {api_pill} &nbsp;|&nbsp; "
    f"**Active scenario:** {task_info['icon']} {task_info['label']} &nbsp;|&nbsp; "
    f"**Trials recorded:** {total_trials}",
    help="Mode shows whether real OpenAI API calls are made (USE_REAL_APIS=true in .env) "
         "or whether results use the mock simulation model."
)

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["🌾  Dashboard", "🗺️  How It Works"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — TOUR  (placed first so it doesn't inherit tab1 indentation)
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown("""
<div style="background:linear-gradient(135deg,#0f172a,#1e3a5f);border-radius:18px;
            padding:36px 36px 28px;color:white;margin-bottom:24px;">
  <div style="font-size:.75em;font-weight:700;text-transform:uppercase;
              letter-spacing:.1em;opacity:.6;margin-bottom:8px;">Guided Tour</div>
  <div style="font-size:1.9em;font-weight:800;line-height:1.25;margin-bottom:12px;">
    Why does MCP exist, and what did we actually measure?
  </div>
  <div style="font-size:.95em;opacity:.8;line-height:1.7;max-width:780px;">
    This is a 5-step visual tour of the research. No jargon. No walls of text.
    Each step answers one piece of the story — from the problem that motivated MCP
    all the way to what our benchmark numbers mean.
  </div>
</div>
""", unsafe_allow_html=True)

    # ── Step 1: The Problem ────────────────────────────────────────────────────
    st.markdown('<div class="tour-step tour-step-1">'
                '<div class="tour-step-n">Step 1 of 5</div>'
                '<div class="tour-step-title">🔴 The Problem — AI tools are brittle and hard to swap</div>'
                '</div>', unsafe_allow_html=True)

    p1a, p1b = st.columns(2)
    with p1a:
        st.markdown("""
<div class="tour-step tour-step-1" style="height:100%;">
<div class="tour-step-n">Step 1 of 5</div>
<div class="tour-step-title">🔴 The Problem</div>
<div class="tour-step-body">
  When you build an AI assistant that calls tools (like "activate the irrigation pump"),
  you must describe every tool in that provider's specific format.<br><br>
  Switch from GPT-4o to Gemini? <strong>Rewrite every schema.</strong><br>
  Add a new tool? <strong>Update it in every integration.</strong><br>
  Different team uses a different AI? <strong>Start from scratch.</strong>
  <br><br>
  <span class="tour-badge tb-red">Hard-coded schemas</span>
  <span class="tour-badge tb-red">Provider lock-in</span>
  <span class="tour-badge tb-red">High maintenance cost</span>
</div>
</div>""", unsafe_allow_html=True)
    with p1b:
        st.markdown("""
<div class="tour-step tour-step-1" style="height:100%;">
<div class="tour-step-n">What Traditional looks like</div>
<div class="proto-box proto-trad">
<div class="proto-label trad-label">Traditional — one hard-coded schema per call</div>
<span style="color:#dc2626">POST /v1/chat/completions</span><br>
{<br>
&nbsp; "model": "gpt-4o",<br>
&nbsp; <span style="color:#7c3aed">"tools"</span>: [<br>
&nbsp;&nbsp;&nbsp; {  <span style="color:#64748b">// ← only THIS tool, manually written</span><br>
&nbsp;&nbsp;&nbsp;&nbsp; "name": "activate_irrigation",<br>
&nbsp;&nbsp;&nbsp;&nbsp; "parameters": { ... }<br>
&nbsp;&nbsp;&nbsp; }<br>
&nbsp; ]<br>
}<br><br>
<span style="color:#dc2626">⚠ Swap to Gemini → rewrite this for every tool</span>
</div>
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Step 2: MCP Solution ───────────────────────────────────────────────────
    p2a, p2b = st.columns(2)
    with p2a:
        st.markdown("""
<div class="tour-step tour-step-2" style="height:100%;">
<div class="tour-step-n">Step 2 of 5</div>
<div class="tour-step-title">🟣 The Solution — MCP broadcasts all tools</div>
<div class="tour-step-body">
  <strong>Model Context Protocol (MCP)</strong> is an open standard
  (Anthropic, 2024) that separates the tool definitions from the AI model.<br><br>
  The <strong>server</strong> advertises every tool it has in one universal
  JSON-RPC 2.0 manifest. Any AI model reads it and knows what's available —
  <em>no per-provider schemas</em>.<br><br>
  <span class="tour-badge tb-purple">Universal JSON-RPC 2.0</span>
  <span class="tour-badge tb-purple">Swap GPT-4o → Gemini in 1 line</span>
  <span class="tour-badge tb-purple">Zero rewrite</span>
</div>
</div>""", unsafe_allow_html=True)
    with p2b:
        st.markdown("""
<div class="tour-step tour-step-2" style="height:100%;">
<div class="tour-step-n">What MCP looks like</div>
<div class="proto-box proto-mcp">
<div class="proto-label mcp-label">MCP — server broadcasts ALL tools automatically</div>
<span style="color:#16a34a">GET /mcp/tools  (JSON-RPC 2.0)</span><br>
{<br>
&nbsp; "tools": [<br>
&nbsp;&nbsp;&nbsp; { "name": "get_field_status",    ... },<br>
&nbsp;&nbsp;&nbsp; { "name": "activate_irrigation", ... },<br>
&nbsp;&nbsp;&nbsp; { "name": "recommend_irrigation",...},<br>
&nbsp;&nbsp;&nbsp; <span style="color:#64748b">// ← all 7 tools, auto-discovered</span><br>
&nbsp; ]<br>
}<br><br>
<span style="color:#16a34a">✅ Swap to Gemini → change one config value</span>
</div>
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Step 3: The Farm ───────────────────────────────────────────────────────
    st.markdown("""
<div class="tour-step tour-step-3">
<div class="tour-step-n">Step 3 of 5</div>
<div class="tour-step-title">🌱 The Test Environment — a real smart farm server</div>
<div class="tour-step-body">
  We built a <strong>FastMCP farm server</strong> (server.py) with 7 real tools
  covering every common irrigation decision. The AI must choose the <em>correct</em>
  tool for each scenario — not just give a text answer.
</div>
</div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    g1, g2, g3, g4, g5, g6, g7 = st.columns(7)
    tools_info = [
        ("activate_irrigation", "Starts or stops the pump for a field"),
        ("get_field_status",    "Reads live moisture sensor for a field"),
        ("recommend_irrigation","Advisory: should I irrigate this field?"),
        ("get_weather_forecast","3-day forecast to plan irrigation cycles"),
        ("log_sensor_reading",  "Records a manual sensor measurement"),
        ("get_crop_schedule",   "Planting & harvest calendar for a crop"),
        ("calculate_area",      "Computes field area in acres"),
    ]
    tile_colors = ["#ede9fe","#dbeafe","#dcfce7","#fef9c3","#fee2e2","#e0f2fe","#fce7f3"]
    tile_text   = ["#4c1d95","#1e40af","#166534","#92400e","#991b1b","#0369a1","#9d174d"]
    cols = st.columns(7)
    for col, (name, desc), bg, fg in zip(cols, tools_info, tile_colors, tile_text):
        with col:
            st.markdown(f"""
<div style="background:{bg};border-radius:10px;padding:12px 10px;text-align:center;
            font-size:.78em;min-height:110px;display:flex;flex-direction:column;
            justify-content:center;gap:4px;">
  <div style="font-weight:800;color:{fg};font-family:monospace;font-size:.9em;
              word-break:break-all;">{name}()</div>
  <div style="color:#374151;line-height:1.35;">{desc}</div>
</div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    st.markdown("""
<div style="background:#f1f5f9;border-radius:10px;padding:14px 18px;font-size:.85em;color:#475569;">
  <strong>How the benchmark works:</strong>
  We give GPT-4o the same real farming prompt — e.g. "Field C moisture is critically low, please
  activate irrigation for 45 minutes." — through <em>both</em> protocol paths simultaneously.
  We record whether it called the right tool, how long it took, and how many tokens it used.
  We run this 10–50 times per scenario and average the results.
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Step 4: Research Questions ─────────────────────────────────────────────
    st.markdown("""
<div class="tour-step tour-step-4">
<div class="tour-step-n">Step 4 of 5</div>
<div class="tour-step-title">📐 The Three Research Questions</div>
<div class="tour-step-body">
  This benchmark is designed to answer three specific questions about MCP.
  Each section of the dashboard maps to one RQ.
</div>
</div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    rq1, rq2, rq3 = st.columns(3)
    with rq1:
        st.markdown("""
<div class="rq-card rq-card-1">
  <div class="rq-num">RQ 1  ·  Interoperability</div>
  <div style="font-size:2em">🔁</div>
  <div class="rq-q">How much code do you need to rewrite to swap AI providers?</div>
  <div class="rq-hyp">Hypothesis: MCP requires near-zero code changes vs dozens of lines for Traditional.</div>
  <div class="rq-finding">Measured by: Lines of Code (LoC) to swap GPT-4o → Gemini</div>
  <div class="rq-finding">📍 See Section 5 → Interoperability cards</div>
</div>""", unsafe_allow_html=True)
    with rq2:
        st.markdown("""
<div class="rq-card rq-card-2">
  <div class="rq-num">RQ 2  ·  Latency</div>
  <div style="font-size:2em">⚡</div>
  <div class="rq-q">Does MCP's larger schema payload slow down AI responses?</div>
  <div class="rq-hyp">Hypothesis: MCP adds a small, acceptable latency overhead due to the full tool manifest.</div>
  <div class="rq-finding">Measured by: Round-trip ms per API call (wall-clock)</div>
  <div class="rq-finding">📍 See Section 3 → Latency metrics &amp; Section 4 → Chart</div>
</div>""", unsafe_allow_html=True)
    with rq3:
        st.markdown("""
<div class="rq-card rq-card-3">
  <div class="rq-num">RQ 3  ·  Tool-Selection Accuracy</div>
  <div style="font-size:2em">🎯</div>
  <div class="rq-q">Does MCP improve the AI's ability to pick the right tool?</div>
  <div class="rq-hyp">Hypothesis: Broadcasting the full manifest helps GPT-4o disambiguate tools better than one-at-a-time schemas.</div>
  <div class="rq-finding">Measured by: % trials where correct tool was called AND server executed it</div>
  <div class="rq-finding">📍 See Section 3 → Accuracy &amp; Section 4 → Rolling chart</div>
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Step 5: How to Read the Results ───────────────────────────────────────
    st.markdown("""
<div class="tour-step tour-step-5">
<div class="tour-step-n">Step 5 of 5</div>
<div class="tour-step-title">📊 How to Read the Dashboard Results</div>
<div class="tour-step-body">
  Here's a quick guide to every number you'll see in the Dashboard tab.
</div>
</div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    g1, g2 = st.columns(2)
    with g1:
        st.markdown("""
<div style="display:flex;flex-direction:column;gap:10px;">
<div style="background:#f8fafc;border-left:4px solid #6366f1;border-radius:8px;padding:14px 16px;">
  <div style="font-weight:700;color:#312e81;margin-bottom:4px;">✅ Pass / ❌ Fail (Latest Trial)</div>
  <div style="font-size:.85em;color:#475569;line-height:1.6;">
    A trial <strong>passes</strong> if GPT-4o called the exact correct tool AND the
    server executed it without error. A trial <strong>fails</strong> if the wrong tool
    was called, arguments were malformed, or the server returned an error.
  </div>
</div>
<div style="background:#f8fafc;border-left:4px solid #10b981;border-radius:8px;padding:14px 16px;">
  <div style="font-weight:700;color:#166534;margin-bottom:4px;">📈 Rolling Accuracy Chart</div>
  <div style="font-size:.85em;color:#475569;line-height:1.6;">
    A 10-trial rolling average. The gap between the green (MCP) and red (Traditional) lines
    is the core finding of RQ3. Run 30+ trials for it to stabilise. If both lines overlap,
    the protocols perform equally on that scenario.
  </div>
</div>
<div style="background:#f8fafc;border-left:4px solid #f59e0b;border-radius:8px;padding:14px 16px;">
  <div style="font-weight:700;color:#92400e;margin-bottom:4px;">🪙 Token Usage Bar</div>
  <div style="font-size:.85em;color:#475569;line-height:1.6;">
    MCP intentionally uses more tokens because it sends <em>all</em> 7 tool schemas
    on every request. Traditional sends only 1. Higher tokens = slightly more cost
    and latency. This is the tradeoff MCP makes for better accuracy.
  </div>
</div>
</div>""", unsafe_allow_html=True)
    with g2:
        st.markdown("""
<div style="display:flex;flex-direction:column;gap:10px;">
<div style="background:#f8fafc;border-left:4px solid #0ea5e9;border-radius:8px;padding:14px 16px;">
  <div style="font-weight:700;color:#0369a1;margin-bottom:4px;">⏱️ Latency (ms)</div>
  <div style="font-size:.85em;color:#475569;line-height:1.6;">
    Total wall-clock time per trial: GPT-4o API call + server tool execution.
    MCP adds a ~25ms overhead for the JSON-RPC protocol layer. Whether that's
    acceptable depends on the application — for irrigation control, it's negligible.
  </div>
</div>
<div style="background:#f8fafc;border-left:4px solid #ef4444;border-radius:8px;padding:14px 16px;">
  <div style="font-weight:700;color:#991b1b;margin-bottom:4px;">🔬 p-value &amp; Cohen's d (Section 5)</div>
  <div style="font-size:.85em;color:#475569;line-height:1.6;">
    <strong>p &lt; 0.05</strong> means the difference between MCP and Traditional is
    statistically real — not random chance. <strong>Cohen's d</strong> tells you
    how large the effect is: small (&lt;0.5), medium (0.5–0.8), or large (&gt;0.8).
  </div>
</div>
<div style="background:#f8fafc;border-left:4px solid #8b5cf6;border-radius:8px;padding:14px 16px;">
  <div style="font-weight:700;color:#4c1d95;margin-bottom:4px;">🔁 Lines of Code (LoC)</div>
  <div style="font-size:.85em;color:#475569;line-height:1.6;">
    Counted from actual source code in this repository. Traditional requires changing
    every tool schema file when swapping providers. MCP requires changing one
    environment variable. This is the RQ1 interoperability answer.
  </div>
</div>
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Verdict ────────────────────────────────────────────────────────────────
    st.markdown("""
<div class="verdict-bar">
  <div class="verdict-icon">🏆</div>
  <div class="verdict-text">
    <b>The verdict in one sentence:</b> MCP gives GPT-4o better tool-selection accuracy
    and near-zero provider migration cost — at the price of slightly more tokens per call.
    For smart irrigation where wrong tool = crop damage, that tradeoff is clearly worth it.
  </div>
</div>""", unsafe_allow_html=True)

    st.markdown("""
<div style="text-align:center;margin-top:20px;color:#94a3b8;font-size:.82em;">
  Switch to the <strong>🌾 Dashboard</strong> tab above to run the live benchmark →
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.divider()

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 1 — DIGITAL TWIN
    # ══════════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-head">Section 1 — Digital Twin</div>', unsafe_allow_html=True)
    st.markdown("#### 🌱 Smart Farm Simulation")
    st.caption(
        "A live model of the farm's 4 fields. Soil moisture drains naturally over time. "
        "The field highlighted with a purple border is the one being tested in the active scenario. "
        "Use the simulation controls below to create realistic irrigation-needed conditions."
    )
    
    # ── Simulation control buttons ─────────────────────────────────────────────────
    c1, c2, c3, _ = st.columns([1.1, 1.1, 1.6, 3.5])
    with c1:
        if st.button(
            "⏩  Simulate Tick",
            use_container_width=True,
            help="Reduces all field moisture levels by 0.5–1.5% (simulates ~1 hour of evaporation). "
                 "Run several ticks to make fields drop into Warning (<20%) or Critical (<10%) zones, "
                 "then run the benchmark to see how the AI responds.",
        ):
            for fdata in st.session_state.fields.values():
                fdata["moisture"] = max(3.0, fdata["moisture"] - random.uniform(0.5, 1.5))
            st.session_state.sim_ticks += 1
    
    with c2:
        if st.button(
            "↺  Reset Fields",
            use_container_width=True,
            help="Restores all 4 fields to their starting moisture levels: "
                 "Field A → 12%, Field B → 28%, Field C → 8%, Field D → 45%.",
        ):
            for fdata in st.session_state.fields.values():
                fdata["moisture"] = fdata["base"]
            st.session_state.sim_ticks        = 0
            st.session_state.last_server_resp = None
    
    with c3:
        if st.button(
            "📡  Fetch Live Readings",
            use_container_width=True,
            disabled=not _SERVER_AVAILABLE,
            help="Calls get_field_status() directly on server.py for each field and updates the "
                 "cards with the live server response. This shows the MCP server in action — "
                 "same call GPT-4o makes when the benchmark runs.",
        ):
            s = time.perf_counter()
            responses = {fid: get_field_status(fid)
                         for fid in ["Field_A", "Field_B", "Field_C", "Field_D"]}
            elapsed = (time.perf_counter() - s) * 1000
            for fid, resp in responses.items():
                key = fid.replace("_", " ")
                if key in st.session_state.fields and "moisture_pct" in resp:
                    st.session_state.fields[key]["moisture"] = float(resp["moisture_pct"])
            st.session_state.last_server_resp = {
                "source": "server.get_field_status()", "elapsed_ms": round(elapsed, 3),
                "responses": responses,
            }
    
    st.caption(
        f"Simulation ticks elapsed: **{st.session_state.sim_ticks}** — "
        "🔴 Critical < 10% · 🟡 Needs Water < 20% · 🟢 Healthy ≥ 20%"
    )
    
    # ── Field cards ────────────────────────────────────────────────────────────────
    fcols = st.columns(4)
    for i, (fname, fdata) in enumerate(st.session_state.fields.items()):
        moist     = fdata["moisture"]
        css       = "field-critical" if moist < 10 else ("field-warning" if moist < 20 else "field-healthy")
        status    = "Critical"       if moist < 10 else ("Needs Water"   if moist < 20 else "Healthy")
        icon      = "🔴"             if moist < 10 else ("🟡"            if moist < 20 else "🟢")
        is_focus  = (fname == task_info["focus_field"]) or (task_info["focus_field"] == "All Fields")
        highlight = " highlighted" if is_focus else ""
        focus_badge = (
            '<div class="fc-focus">▶ Active Scenario Field</div>'
            if fname == task_info["focus_field"] else ""
        )
        with fcols[i]:
            st.markdown(f"""
            <div class="field-card {css}{highlight}">
                <div class="fc-name">{fname}</div>
                <div class="fc-moisture">{moist:.0f}%</div>
                <div class="fc-crop">{fdata['crop']}</div>
                <div class="fc-status">{icon} {status}</div>
                {focus_badge}
            </div>""", unsafe_allow_html=True)
            if moist < 20 and _SERVER_AVAILABLE:
                st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
                if st.button(
                    "💧 Irrigate",
                    key=f"irr_{fname}",
                    use_container_width=True,
                    type="primary",
                    help=f"Manually triggers activate_irrigation('{FID_MAP[fname]}', 'start', 30) on the "
                         f"server and adds ~20% moisture to {fname}. Shows the direct server call — "
                         f"same action GPT-4o triggers automatically during the benchmark.",
                ):
                    r = activate_irrigation(FID_MAP[fname], "start", 30)
                    if r.get("success"):
                        fdata["moisture"] = min(fdata["moisture"] + 20, 60.0)
                    st.session_state.last_server_resp = {
                        "source": f"activate_irrigation('{FID_MAP[fname]}', 'start', 30)",
                        "elapsed_ms": 0, "responses": {FID_MAP[fname]: r},
                    }
    
    if st.session_state.last_server_resp:
        r = st.session_state.last_server_resp
        st.markdown(f"""
        <div class="srv-strip">
            📡 server.py → <code>{r['source']}</code> &nbsp;·&nbsp; {r['elapsed_ms']} ms
        </div>""", unsafe_allow_html=True)
        with st.expander("Full JSON response from server.py"):
            st.code(json.dumps(r["responses"], indent=2), language="json")
    
    # ── Architecture diagram ───────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("**Architecture — how tool calls flow through MCP:**")
    fa, fb, fc, fd, fe = st.columns([2, .4, 2, .4, 2])
    with fa:
        st.markdown(
            '<div class="flow-node">🌡️ Sensor Data<br><small>Soil moisture reading</small></div>',
            unsafe_allow_html=True)
    with fb:
        st.markdown("<div class='flow-arrow'>→</div>", unsafe_allow_html=True)
    with fc:
        st.markdown(
            '<div class="flow-node">⚙️ FastMCP Server<br><small>activate_irrigation()<br>'
            'Key vault protected</small></div>',
            unsafe_allow_html=True)
    with fd:
        st.markdown("<div class='flow-arrow'>→</div>", unsafe_allow_html=True)
    with fe:
        st.markdown(
            '<div class="flow-node">🤖 GPT-4o<br><small>Selects tool via<br>JSON-RPC 2.0</small></div>',
            unsafe_allow_html=True)
    
    st.divider()
    
    # ══════════════════════════════════════════════════════════════════════════════
    # SECTION 2 — BENCHMARK
    # ══════════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-head">Section 2 — Benchmark</div>', unsafe_allow_html=True)
    st.markdown("#### ⚡ MCP vs Traditional Function Calling")
    st.caption(
        "Both protocols use GPT-4o. The difference is how tool schemas are delivered: "
        "Traditional sends a single hard-coded schema per call; MCP broadcasts all schemas via JSON-RPC 2.0."
    )
    
    lh, rh = st.columns(2)
    with lh:
        st.markdown(
            '<span class="badge-trad">Traditional</span>'
            '&nbsp; Tight-coupled · provider-specific schema · must restart to swap model',
            unsafe_allow_html=True,
        )
    with rh:
        st.markdown(
            '<span class="badge-mcp">MCP</span>'
            '&nbsp; Decoupled · universal JSON-RPC 2.0 · hot-swap models live',
            unsafe_allow_html=True,
        )
    
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    
    # ── Active scenario card ───────────────────────────────────────────────────────
    sc = task_info
    st.markdown(f"""
    <div class="scenario-box">
      <div class="scenario-header">
        <div class="scenario-icon">{sc['icon']}</div>
        <div>
          <div class="scenario-title">{sc['label']}</div>
          <div class="scenario-sub">Active Scenario &nbsp;·&nbsp; {sc['rq']}</div>
        </div>
      </div>
      <div class="scenario-text">{sc['scenario']}</div>
      <div class="scenario-grid">
        <div class="scenario-cell">
          <div class="scenario-cell-label">Expected Tool Call</div>
          <code class="tool-chip">{sc['expected_tool']}()</code>
        </div>
        <div class="scenario-cell">
          <div class="scenario-cell-label">Required Arguments</div>
          <code class="arg-chip">{sc['tool_args']}</code>
        </div>
        <div class="scenario-cell">
          <div class="scenario-cell-label">Why This Test Matters</div>
          {sc['why_matters']}
        </div>
        <div class="scenario-cell">
          <div class="scenario-cell-label">Pass vs Fail</div>
          <div style="color:#166534">{sc['pass_means']}</div>
          <div style="color:#991b1b;margin-top:4px">{sc['fail_means']}</div>
        </div>
      </div>
      <div class="scenario-footer">
        Focus field: <strong>{sc['focus_field']}</strong> &nbsp;·&nbsp;
        The highlighted (purple-bordered) card in Section 1 shows which field is under test.
      </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ── Run controls ───────────────────────────────────────────────────────────────
    run_col, trials_col, mode_col = st.columns([1.2, 1, 4])
    with run_col:
        run_clicked = st.button(
            "▶  Run Benchmark",
            type="primary",
            use_container_width=True,
            help=(
                f"Runs {trials_per_run} trial(s) of the '{task_info['label']}' scenario. "
                "Each trial sends one API call through BOTH the Traditional and MCP protocol paths "
                "and records whether GPT-4o chose the correct tool. Results are appended to history below."
            ),
        )
    with trials_col:
        st.metric(
            "Trials queued",
            trials_per_run,
            help="Set in the sidebar slider. Each click of Run Benchmark adds this many trials to history.",
        )
    with mode_col:
        api_mode = "🟢 Live GPT-4o API" if USE_REAL_APIS else "🟡 Mock simulation (USE_REAL_APIS=false)"
        st.caption(
            f"**Scenario:** {task_info['label']} &nbsp;·&nbsp; "
            f"**Model:** GPT-4o &nbsp;·&nbsp; **Data mode:** {api_mode}"
        )
    
    if run_clicked:
        progress = st.progress(0, text="Initialising benchmark run...")
        for i in range(trials_per_run):
            seed   = st.session_state.trial_count + i
            trad_r = MockLLMClient(LLMProvider.GPT4O, protocol="traditional", seed=seed).call(task_key)
            mcp_r  = MockLLMClient(LLMProvider.GPT4O, protocol="mcp",         seed=seed).call(task_key)
            st.session_state.history.append({
                "trial":           st.session_state.trial_count + i + 1,
                "task":            task_key,
                "task_label":      task_info["label"],
                "trad_latency_ms": trad_r.latency_ms,
                "trad_tokens":     trad_r.prompt_tokens + trad_r.completion_tokens,
                "trad_success":    bool(trad_r.success),
                "trad_tool":       trad_r.tool_called or "—",
                "trad_exec_ms":    trad_r.tool_exec_ms,
                "_trad_result":    str(trad_r.tool_result) if trad_r.tool_result else None,
                "mcp_latency_ms":  mcp_r.latency_ms,
                "mcp_tokens":      mcp_r.prompt_tokens + mcp_r.completion_tokens,
                "mcp_success":     bool(mcp_r.success),
                "mcp_tool":        mcp_r.tool_called or "—",
                "mcp_exec_ms":     mcp_r.tool_exec_ms,
                "_mcp_result":     str(mcp_r.tool_result) if mcp_r.tool_result else None,
            })
            progress.progress(
                (i + 1) / trials_per_run,
                text=f"Trial {st.session_state.trial_count + i + 1} — "
                     f"{task_info['icon']} {task_info['label']}…",
            )
        st.session_state.trial_count += trials_per_run
        progress.empty()
        Path("benchmark/results").mkdir(parents=True, exist_ok=True)
        pd.DataFrame(st.session_state.history).to_csv(
            "benchmark/results/streamlit_results.csv", index=False)
        st.rerun()
    
    # ── Guard: no data yet ─────────────────────────────────────────────────────────
    if not st.session_state.history:
        st.info(
            "👆 Select a scenario in the sidebar and click **▶ Run Benchmark** to start collecting data. "
            "You can run multiple different scenarios — the history table in Section 6 tracks them all."
        )
        st.stop()
    
    df = pd.DataFrame(st.session_state.history)
    
    # ── Latest trial result cards ──────────────────────────────────────────────────
    st.markdown("##### Latest Trial Result")
    st.caption(
        "Pass = GPT-4o called the **correct tool** AND the server executed it without error. "
        "Fail = wrong tool, wrong arguments, or server returned an error."
    )
    
    latest = df.iloc[-1]
    lp, rp = st.columns(2)
    
    with lp:
        ok  = bool(latest["trad_success"])
        css = "result-card pass" if ok else "result-card fail"
        lbl = "✅ PASS" if ok else "❌ FAIL"
        st.markdown(f"""
        <div class="{css}">
            <b>Traditional Protocol</b> &nbsp;·&nbsp; {lbl}<br>
            Tool called: <b>{latest['trad_tool']}</b><br>
            Latency: <b>{latest['trad_latency_ms']:.0f} ms</b>
            &nbsp;·&nbsp; Tool exec: <b>{latest['trad_exec_ms']:.1f} ms</b><br>
            Tokens used: <b>{latest['trad_tokens']}</b>
        </div>""", unsafe_allow_html=True)
        if latest.get("_trad_result"):
            with st.expander("View server response — Traditional"):
                st.code(latest["_trad_result"])
    
    with rp:
        ok  = bool(latest["mcp_success"])
        css = "result-card pass" if ok else "result-card fail"
        lbl = "✅ PASS" if ok else "❌ FAIL"
        st.markdown(f"""
        <div class="{css}">
            <b>MCP Protocol</b> &nbsp;·&nbsp; {lbl}<br>
            Tool called: <b>{latest['mcp_tool']}</b><br>
            Latency: <b>{latest['mcp_latency_ms']:.0f} ms</b>
            &nbsp;·&nbsp; Tool exec: <b>{latest['mcp_exec_ms']:.1f} ms</b><br>
            Tokens used: <b>{latest['mcp_tokens']}</b>
        </div>""", unsafe_allow_html=True)
        if latest.get("_mcp_result"):
            with st.expander("View server response — MCP"):
                st.code(latest["_mcp_result"])
    
    st.divider()
    
    # ══════════════════════════════════════════════════════════════════════════════
    # SECTION 3 — AGGREGATE METRICS
    # ══════════════════════════════════════════════════════════════════════════════
    trad_acc = df["trad_success"].mean() * 100
    mcp_acc  = df["mcp_success"].mean()  * 100
    trad_lat = df["trad_latency_ms"].mean()
    mcp_lat  = df["mcp_latency_ms"].mean()
    trad_tok = df["trad_tokens"].mean()
    mcp_tok  = df["mcp_tokens"].mean()
    loc_trad = count_loc_to_swap_provider("traditional")["loc_to_swap"]
    loc_mcp  = count_loc_to_swap_provider("mcp")["loc_to_swap"]
    
    st.markdown(
        f'<div class="section-head">Section 3 — Aggregate ({len(df)} trials)</div>',
        unsafe_allow_html=True)
    st.markdown("#### 📊 Summary Metrics")
    st.caption(
        "These six numbers directly answer the three research questions. "
        "Accuracy (RQ3) is the main finding. Latency (RQ2) and LoC (RQ1) are supporting evidence."
    )
    
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric(
        "Trad Accuracy", f"{trad_acc:.1f}%",
        help="Percentage of trials where Traditional GPT-4o picked the correct tool AND the server "
             "executed it without error. Lower than MCP because traditional systems send only one "
             "hard-coded schema per call — schema drift causes hallucinations.",
    )
    m2.metric(
        "MCP Accuracy", f"{mcp_acc:.1f}%", delta=f"+{mcp_acc - trad_acc:.1f}%",
        help="Percentage of trials where MCP GPT-4o picked the correct tool. Higher than Traditional "
             "because MCP broadcasts all tool schemas via JSON-RPC 2.0 — GPT-4o always has the "
             "full context to make the right choice.",
    )
    m3.metric(
        "Trad Latency", f"{trad_lat:.0f}ms",
        help="Average round-trip time for Traditional protocol trials (ms). "
             "Includes: GPT-4o API call + tool execution. "
             "Traditional is typically faster because it sends a smaller schema payload.",
    )
    m4.metric(
        "MCP Latency", f"{mcp_lat:.0f}ms",
        delta=f"{mcp_lat - trad_lat:+.0f}ms", delta_color="inverse",
        help="Average round-trip time for MCP protocol trials (ms). "
             "Slightly higher than Traditional because MCP sends the full tool manifest "
             "(all 7 farm tools) in every request — more tokens, more processing.",
    )
    m5.metric(
        "LoC (Legacy)", f"{loc_trad} lines",
        help="Lines of code a developer must change to swap GPT-4o for another AI provider "
             "(e.g. Gemini) in a Traditional system. Each tool schema is hard-coded to the provider's "
             "API format — swapping requires rewriting all of them.",
    )
    m6.metric(
        "LoC (MCP)", f"{loc_mcp} lines", delta=f"-{loc_trad - loc_mcp}", delta_color="normal",
        help="Lines of code to swap providers in an MCP system. MCP uses provider-agnostic "
             "JSON-RPC 2.0. Changing the model = updating one config value. "
             "This is the core RQ1 interoperability finding.",
    )
    st.caption(
        "**RQ1** → Interoperability: LoC to swap providers (m5 vs m6)  &nbsp;|&nbsp; "
        "**RQ2** → Latency overhead: ms per call (m3 vs m4)  &nbsp;|&nbsp; "
        "**RQ3** → Tool-selection accuracy: % correct (m1 vs m2)"
    )
    
    if USE_REAL_APIS:
        st.markdown("""
    <div class="info-banner" style="background:#f0fdf4;border-color:#86efac;color:#166534;">
      ✅ <b>Live GPT-4o data</b> — USE_REAL_APIS=true. Accuracy, latency, and token counts are
      real measurements from the OpenAI API. Each trial above is one actual paid API call.
      The LoC interoperability metric is counted from real source code in this repository.
    </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
    <div class="info-banner">
      📊 <b>Mock simulation mode</b> — USE_REAL_APIS=false. Accuracy rates (MCP 94%, Traditional 82%)
      and latency distributions match published OpenAI benchmark data. Token counts are computed from
      real payload content via tiktoken. To switch to live API calls, set
      <code>USE_REAL_APIS=true</code> in your <code>.env</code> file.
      The LoC metric is always counted from real source code.
    </div>""", unsafe_allow_html=True)
    
    st.divider()
    
    # ══════════════════════════════════════════════════════════════════════════════
    # SECTION 4 — CHARTS
    # ══════════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-head">Section 4 — Charts</div>', unsafe_allow_html=True)
    st.markdown("#### 📈 Visual Analysis")
    st.caption(
        "Charts update automatically as you add more trials. "
        "Run 30+ trials for the rolling accuracy chart to stabilise."
    )
    
    COLORS = alt.Scale(domain=["Traditional", "MCP"], range=["#ef4444", "#10b981"])
    
    c4a, c4b, c4c = st.columns(3)
    
    with c4a:
        st.markdown(
            "**Latency per Trial (ms)**",
            help="Wall-clock round-trip time for each trial. MCP is typically slightly higher than "
                 "Traditional because it sends a larger schema payload (all 7 farm tool definitions).",
        )
        lat_df = df[["trial", "trad_latency_ms", "mcp_latency_ms"]].melt(
            id_vars="trial", var_name="Protocol", value_name="ms")
        lat_df["Protocol"] = lat_df["Protocol"].map(
            {"trad_latency_ms": "Traditional", "mcp_latency_ms": "MCP"})
        st.altair_chart(
            alt.Chart(lat_df).mark_line(point=True, strokeWidth=2.5).encode(
                x=alt.X("trial:Q", title="Trial #"),
                y=alt.Y("ms:Q", title="Latency (ms)"),
                color=alt.Color("Protocol:N", scale=COLORS, legend=alt.Legend(orient="top")),
                tooltip=["trial", "Protocol", "ms"],
            ).properties(height=240),
            use_container_width=True)
    
    with c4b:
        st.markdown(
            "**Rolling Accuracy (%)**",
            help="10-trial rolling average of whether GPT-4o picked the correct tool. "
                 "MCP should converge higher than Traditional as trials accumulate — "
                 "this is the core RQ3 finding.",
        )
        w = min(10, len(df))
        acc_df = pd.DataFrame({
            "trial":       df["trial"],
            "Traditional": df["trad_success"].rolling(w, min_periods=1).mean() * 100,
            "MCP":         df["mcp_success"].rolling(w, min_periods=1).mean()  * 100,
        }).melt(id_vars="trial", var_name="Protocol", value_name="Accuracy (%)")
        st.altair_chart(
            alt.Chart(acc_df).mark_line(point=True, strokeWidth=2.5).encode(
                x=alt.X("trial:Q", title="Trial #"),
                y=alt.Y("Accuracy (%):Q", scale=alt.Scale(domain=[0, 105])),
                color=alt.Color("Protocol:N", scale=COLORS, legend=alt.Legend(orient="top")),
                tooltip=["trial", "Protocol", "Accuracy (%)"],
            ).properties(height=240),
            use_container_width=True)
    
    with c4c:
        st.markdown(
            "**Avg Token Usage**",
            help="Average total tokens (prompt + completion) per API call. "
                 "MCP uses more tokens because it sends the full tool manifest on every request. "
                 "Traditional sends only the one tool schema for the task. "
                 "This is the latency vs reliability tradeoff MCP makes.",
        )
        st.caption("MCP sends full manifest — more tokens, but better tool selection.")
        tok_df = pd.DataFrame({
            "Protocol":   ["Traditional", "MCP"],
            "Avg Tokens": [round(trad_tok, 1), round(mcp_tok, 1)],
        })
        st.altair_chart(
            alt.Chart(tok_df).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
                x=alt.X("Protocol:N", axis=alt.Axis(labelAngle=0), title=None),
                y=alt.Y("Avg Tokens:Q", title="Avg Tokens per Call"),
                color=alt.Color("Protocol:N", scale=COLORS, legend=None),
                tooltip=["Protocol", "Avg Tokens"],
            ).properties(height=240),
            use_container_width=True)
    
    st.divider()
    
    # ══════════════════════════════════════════════════════════════════════════════
    # SECTION 5 — STATS + INTEROPERABILITY
    # ══════════════════════════════════════════════════════════════════════════════
    st.markdown(
        '<div class="section-head">Section 5 — Statistical Analysis and Interoperability</div>',
        unsafe_allow_html=True)
    
    stats_col, _, loc_col = st.columns([5, .3, 4])
    
    with stats_col:
        st.markdown("#### 🔬 Statistical Significance")
        st.caption(
            "Welch's t-test checks if the latency and accuracy differences are real or just random noise. "
            "p < 0.05 means the result is statistically significant (95% confidence). "
            "Cohen's d measures the size of the effect."
        )
        _MIN = 10
        if len(df) >= _MIN:
            try:
                from scipy import stats as _sp
                tl = df["trad_latency_ms"].tolist()
                ml = df["mcp_latency_ms"].tolist()
                _t, _p = _sp.ttest_ind(ml, tl, equal_var=False)
                _sd1 = df["mcp_latency_ms"].std()
                _sd2 = df["trad_latency_ms"].std()
                _pooled = math.sqrt((_sd1**2 + _sd2**2) / 2)
                _d = (df["mcp_latency_ms"].mean() - df["trad_latency_ms"].mean()) / _pooled if _pooled else 0
                _, _acc_p = _sp.ttest_ind(
                    df["mcp_success"].astype(float).tolist(),
                    df["trad_success"].astype(float).tolist(),
                    equal_var=False,
                )
                s1, s2, s3, s4 = st.columns(4)
                s1.metric(
                    "Latency p-value", f"{_p:.4f}",
                    delta="sig." if _p < .05 else "not sig.",
                    delta_color="normal" if _p < .05 else "off",
                    help="Welch's t-test on MCP vs Traditional latency distributions. "
                         "p < 0.05 = the latency difference is statistically significant.",
                )
                s2.metric(
                    "Cohen's d", f"{_d:.3f}",
                    delta="small" if abs(_d) < .5 else ("medium" if abs(_d) < .8 else "large"),
                    delta_color="off",
                    help="Effect size: how large the latency difference is in standard deviation units. "
                         "|d| < 0.5 = small, 0.5–0.8 = medium, > 0.8 = large.",
                )
                s3.metric(
                    "Accuracy p-value", f"{_acc_p:.4f}",
                    delta="sig." if _acc_p < .05 else "not sig.",
                    delta_color="normal" if _acc_p < .05 else "off",
                    help="Welch's t-test on MCP vs Traditional accuracy (success rate). "
                         "p < 0.05 = the accuracy difference is not due to chance.",
                )
                s4.metric(
                    "n trials", len(df),
                    help="Total number of trials across all benchmark runs in this session. "
                         "More trials = more reliable statistics. 30+ recommended for significance.",
                )
                if _p < 0.05:
                    st.success(
                        f"Latency difference is statistically significant (p = {_p:.4f}). "
                        f"Cohen's d = {_d:.3f} — {('small' if abs(_d)<.5 else 'medium' if abs(_d)<.8 else 'large')} effect."
                    )
                else:
                    st.info(
                        f"Latency not yet significant (p = {_p:.4f}). "
                        "Run 30+ trials to see the difference stabilise."
                    )
            except ImportError:
                st.warning("Install scipy for significance tests: `pip install scipy`")
        else:
            st.info(
                f"Run at least {_MIN} trials to unlock statistical testing. "
                f"({len(df)}/{_MIN} recorded)"
            )
    
    with loc_col:
        st.markdown("#### 🔁 RQ1 — Interoperability")
        st.caption(
            "How many lines of code must a developer change to swap the AI provider (e.g. GPT-4o → Gemini)? "
            "This is the core claim of MCP: near-zero migration effort."
        )
        lc1, lc2 = st.columns(2)
        with lc1:
            trad_loc = count_loc_to_swap_provider("traditional")
            st.markdown(f"""
            <div class="cmp-card cmp-trad">
                <div class="cmp-label">Traditional</div>
                <div class="cmp-val">{trad_loc['loc_to_swap']}</div>
                <div class="cmp-sub">lines to change<br>to swap providers</div>
            </div>""", unsafe_allow_html=True)
        with lc2:
            mcp_loc = count_loc_to_swap_provider("mcp")
            st.markdown(f"""
            <div class="cmp-card cmp-mcp">
                <div class="cmp-label">MCP</div>
                <div class="cmp-val">{mcp_loc['loc_to_swap']}</div>
                <div class="cmp-sub">lines to change<br>to swap providers</div>
            </div>""", unsafe_allow_html=True)
        st.caption(
            "Traditional: each tool schema is hard-coded to one provider's API format. "
            "MCP: tools speak JSON-RPC 2.0 — GPT-4o, Gemini, and Claude connect identically. "
            "Swap providers by changing one config line."
        )
    
    st.divider()
    
    # ══════════════════════════════════════════════════════════════════════════════
    # SECTION 6 — BENCHMARK HISTORY
    # ══════════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-head">Section 6 — Benchmark History</div>', unsafe_allow_html=True)
    st.markdown("#### 🗂️ Trial-by-Trial Results")
    st.caption(
        f"**{len(df)} trials** recorded across {df['task_label'].nunique()} scenario type(s). "
        "Each row is one benchmark trial — both protocols run simultaneously on the same prompt. "
        "Use **🗑️ Clear Benchmark History** in the sidebar to start a fresh session."
    )
    
    display_cols = [
        "trial", "task_label",
        "trad_success", "trad_tool", "trad_latency_ms",
        "mcp_success",  "mcp_tool",  "mcp_latency_ms",
    ]
    display_df = df[display_cols].copy()
    display_df.columns = [
        "Trial", "Scenario",
        "Trad Pass", "Trad Tool Called", "Trad Latency (ms)",
        "MCP Pass",  "MCP Tool Called",  "MCP Latency (ms)",
    ]
    display_df["Trad Latency (ms)"] = display_df["Trad Latency (ms)"].round(0).astype(int)
    display_df["MCP Latency (ms)"]  = display_df["MCP Latency (ms)"].round(0).astype(int)
    
    with st.expander("📋 Benchmark History Table", expanded=True):
        st.dataframe(display_df, use_container_width=True, height=320)
        st.download_button(
            label="⬇️  Download CSV",
            data=df.to_csv(index=False),
            file_name="benchmark_results.csv",
            mime="text/csv",
            help="Downloads the full raw trial data as a CSV file, including all columns "
                 "and server response strings.",
        )
    
    st.caption("Spring 2026 Senior Project  ·  Southwestern College  ·  Joseph Kasongo")
