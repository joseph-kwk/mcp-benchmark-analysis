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
  [data-testid="stSidebar"] { min-width: 260px; }
  .field-card {
    border-radius: 16px; padding: 22px 14px; text-align: center;
    color: white; min-height: 148px;
    display: flex; flex-direction: column; justify-content: center;
    gap: 2px; box-shadow: 0 4px 16px rgba(0,0,0,.12);
    transition: transform .15s ease, box-shadow .15s ease;
  }
  .field-card:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,.18); }
  .field-card.highlighted { box-shadow: 0 0 0 4px #6366f1, 0 8px 24px rgba(0,0,0,.22) !important; }
  .field-healthy  { background: linear-gradient(150deg,#059669,#34d399); }
  .field-warning  { background: linear-gradient(150deg,#d97706,#fbbf24); }
  .field-critical { background: linear-gradient(150deg,#dc2626,#f87171); }
  .fc-name     { font-size: .85em; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; opacity: .9; }
  .fc-moisture { font-size: 2.5em; font-weight: 800; line-height: 1.1; letter-spacing: -.03em; }
  .fc-crop     { font-size: .78em; opacity: .85; margin-top: 2px; }
  .fc-status   { font-size: .75em; background: rgba(255,255,255,.22); border-radius: 20px;
                 padding: 3px 10px; display: inline-block; margin-top: 6px; font-weight: 600; }
  .fc-focus    { font-size: .7em; background: rgba(255,255,255,.35); border-radius: 20px;
                 padding: 2px 8px; display: inline-block; margin-top: 4px; font-weight: 700;
                 text-transform: uppercase; letter-spacing: .05em; }
  .badge-mcp  { display:inline-block; background:#d1fae5; color:#065f46;
                padding:5px 14px; border-radius:20px; font-size:.82em; font-weight:700; }
  .badge-trad { display:inline-block; background:#fee2e2; color:#991b1b;
                padding:5px 14px; border-radius:20px; font-size:.82em; font-weight:700; }
  .result-card {
    background: #f8fafc; border-left: 4px solid #6366f1; border-radius: 8px;
    padding: 16px 18px; font-family: 'SF Mono','Monaco',monospace;
    font-size: .88em; color: #1e293b; line-height: 2;
    box-shadow: 0 1px 4px rgba(0,0,0,.06);
  }
  .result-card.fail { border-left-color: #ef4444; background: #fff5f5; }
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
  .srv-strip {
    background: #f0fdf4; border-left: 4px solid #10b981; border-radius: 8px;
    padding: 10px 16px; font-family: monospace; font-size: .82em;
    color: #1e293b; margin-top: 10px;
  }
  .flow-node {
    background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 10px;
    padding: 12px 16px; text-align: center; font-size: .84em; color: #374151;
    line-height: 1.5;
  }
  .flow-arrow { text-align: center; padding-top: 16px; color: #6366f1;
                font-weight: 700; font-size: 1.3em; }
  .section-head {
    font-size: .72em; font-weight: 700; text-transform: uppercase;
    letter-spacing: .09em; color: #94a3b8; margin-bottom: 2px;
  }
  .info-banner {
    background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px;
    padding: 10px 16px; font-size: .85em; color: #1e40af; margin-top: 6px;
  }
  .scenario-box {
    background: #fafafa; border: 1.5px solid #e2e8f0; border-radius: 10px;
    padding: 14px 18px; margin-bottom: 12px;
  }
  .scenario-label { font-size: .7em; font-weight: 700; text-transform: uppercase;
                    letter-spacing: .08em; color: #6366f1; margin-bottom: 4px; }
  .scenario-text  { font-size: .9em; color: #1e293b; line-height: 1.6; }
  .scenario-meta  { font-size: .78em; color: #64748b; margin-top: 6px; }
  code.tool-chip  { background: #e0e7ff; color: #3730a3; padding: 2px 8px;
                    border-radius: 6px; font-family: monospace; font-size: .85em; }
</style>
""", unsafe_allow_html=True)

# ── Focused task scenarios (irrigation-domain, per advisor guidance) ──────────
TASK_SCENARIOS = {
    "irrigation_check": {
        "label":         "Irrigation Check",
        "scenario":      "Field C soil moisture has dropped to 8%, well below the 20% danger threshold. "
                         "The AI must decide: activate irrigation or not?",
        "expected_tool": "activate_irrigation",
        "focus_field":   "Field C",
        "rq":            "RQ3 — Accuracy: does MCP pick the correct tool more reliably?",
    },
    "field_status": {
        "label":         "Field Status Query",
        "scenario":      "Operator asks: What is the current soil moisture level and health status of Field A? "
                         "The AI must retrieve live sensor data.",
        "expected_tool": "get_field_status",
        "focus_field":   "Field A",
        "rq":            "RQ3 — Accuracy: correct tool selection under a data-query prompt.",
    },
    "recommend_action": {
        "label":         "Irrigation Recommendation",
        "scenario":      "Field A is at 12% moisture — borderline critical. "
                         "Ask the AI for an evidence-based irrigation recommendation.",
        "expected_tool": "recommend_irrigation",
        "focus_field":   "Field A",
        "rq":            "RQ3 — Accuracy: advisory prompts require precise tool routing.",
    },
    "pump_stop": {
        "label":         "Stop Irrigation Pump",
        "scenario":      "Field C has been irrigated for 45 minutes and is now saturated. "
                         "Stop the pump before over-watering damages the crop.",
        "expected_tool": "activate_irrigation",
        "focus_field":   "Field C",
        "rq":            "RQ3 — Accuracy: same tool (activate_irrigation), different intent — stop vs start.",
    },
    "weather_forecast": {
        "label":         "Weather Forecast",
        "scenario":      "Request a 3-day weather forecast to plan the week's irrigation schedule. "
                         "Rain is expected — should we skip tomorrow's cycle?",
        "expected_tool": "get_weather_forecast",
        "focus_field":   "All Fields",
        "rq":            "RQ3 — Accuracy: forecast lookup used to optimize irrigation timing.",
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
    st.caption("Select a task and run size, then click **Run Benchmark** in Section 2.")

    task_key = st.selectbox(
        "Irrigation Task",
        list(TASK_SCENARIOS.keys()),
        format_func=lambda k: TASK_SCENARIOS[k]["label"],
        help="All tasks are irrigation-domain scenarios. Each one tests GPT-4o's tool-selection accuracy.",
    )
    trials_per_run = st.slider("Trials per run", 1, 50, 10)

    st.divider()

    if st.button("🗑 Clear Benchmark History", use_container_width=True,
                 help="Removes all trial results from this session."):
        st.session_state.history     = []
        st.session_state.trial_count = 0
        st.rerun()

    if st.button("↺ Reset Farm Simulation", use_container_width=True,
                 help="Restores all field moisture levels to baseline."):
        for fdata in st.session_state.fields.values():
            fdata["moisture"] = fdata["base"]
        st.session_state.sim_ticks        = 0
        st.session_state.last_server_resp = None
        st.rerun()

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
st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — DIGITAL TWIN
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-head">Section 1 — Digital Twin</div>', unsafe_allow_html=True)
st.markdown("#### Smart Farm Simulation")
st.caption(
    "Soil moisture drains over time. When it drops below threshold, "
    "the LLM must choose and call `activate_irrigation`. "
    "This tool-selection challenge is what the benchmark measures."
)

# Simulation controls
c1, c2, c3, _ = st.columns([1, 1, 1.8, 4])
with c1:
    if st.button("Simulate Tick", use_container_width=True, help="Each tick = ~1 hour evaporation"):
        for fdata in st.session_state.fields.values():
            fdata["moisture"] = max(3.0, fdata["moisture"] - random.uniform(0.5, 1.5))
        st.session_state.sim_ticks += 1
with c2:
    if st.button("Reset Simulation", use_container_width=True,
                 help="Restore all fields to baseline moisture"):
        for fdata in st.session_state.fields.values():
            fdata["moisture"] = fdata["base"]
        st.session_state.sim_ticks        = 0
        st.session_state.last_server_resp = None
with c3:
    if st.button("Fetch from Server", use_container_width=True,
                 disabled=not _SERVER_AVAILABLE,
                 help="Calls get_field_status() on server.py for live readings"):
        s = time.perf_counter()
        responses = {fid: get_field_status(fid)
                     for fid in ["Field_A", "Field_B", "Field_C", "Field_D"]}
        elapsed = (time.perf_counter() - s) * 1000
        _km = {"Field_A": "Field A", "Field_B": "Field B",
               "Field_C": "Field C", "Field D": "Field D"}
        for fid, resp in responses.items():
            key = fid.replace("_", " ")
            if key in st.session_state.fields and "moisture_pct" in resp:
                st.session_state.fields[key]["moisture"] = float(resp["moisture_pct"])
        st.session_state.last_server_resp = {
            "source": "server.get_field_status()", "elapsed_ms": round(elapsed, 3),
            "responses": responses,
        }

st.caption(f"Simulation ticks elapsed: **{st.session_state.sim_ticks}**")

# Field cards — highlight the field relevant to the active task
fcols = st.columns(4)
for i, (fname, fdata) in enumerate(st.session_state.fields.items()):
    moist  = fdata["moisture"]
    css    = "field-critical" if moist < 10 else ("field-warning" if moist < 20 else "field-healthy")
    status = "Critical"       if moist < 10 else ("Needs Water"   if moist < 20 else "Healthy")
    icon   = "🔴"             if moist < 10 else ("🟡"            if moist < 20 else "🟢")
    is_focus = (fname == task_info["focus_field"]) or (task_info["focus_field"] == "All Fields")
    highlight = ' highlighted' if is_focus else ''
    focus_badge = '<div class="fc-focus">▶ Active Task Field</div>' if fname == task_info["focus_field"] else ''
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
            if st.button("Irrigate", key=f"irr_{fname}", use_container_width=True):
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
        server.py → <code>{r['source']}</code> | {r['elapsed_ms']} ms
    </div>""", unsafe_allow_html=True)
    with st.expander("Full JSON response"):
        st.code(json.dumps(r["responses"], indent=2), language="json")

st.markdown("<br>", unsafe_allow_html=True)
st.caption("**Architecture — how tool calls flow through MCP:**")
fa, fb, fc, fd, fe = st.columns([2, .4, 2, .4, 2])
with fa:
    st.markdown('<div class="flow-node">Sensor Data<br><small>Soil moisture</small></div>', unsafe_allow_html=True)
with fb:
    st.markdown("<div class='flow-arrow'>→</div>", unsafe_allow_html=True)
with fc:
    st.markdown('<div class="flow-node">FastMCP Server<br><small>activate_irrigation()<br>Key vault protected</small></div>', unsafe_allow_html=True)
with fd:
    st.markdown("<div class='flow-arrow'>→</div>", unsafe_allow_html=True)
with fe:
    st.markdown('<div class="flow-node">GPT-4o<br><small>Selects tool via<br>JSON-RPC 2.0</small></div>', unsafe_allow_html=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — BENCHMARK
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-head">Section 2 — Benchmark</div>', unsafe_allow_html=True)
st.markdown("#### MCP vs Traditional Function Calling")

lh, rh = st.columns(2)
with lh:
    st.markdown(
        '<span class="badge-trad">Traditional</span>'
        '  Tight-coupled · provider-specific schema · restart to swap model',
        unsafe_allow_html=True)
with rh:
    st.markdown(
        '<span class="badge-mcp">MCP</span>'
        '  Decoupled · universal JSON-RPC 2.0 · hot-swap models live',
        unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Active task scenario card ──────────────────────────────────────────────────
st.markdown(f"""
<div class="scenario-box">
  <div class="scenario-label">▶ Active Scenario: {task_info['label']}</div>
  <div class="scenario-text">{task_info['scenario']}</div>
  <div class="scenario-meta">
    Expected tool: <code class="tool-chip">{task_info['expected_tool']}()</code>
    &nbsp;·&nbsp; Focus field: <strong>{task_info['focus_field']}</strong>
    &nbsp;·&nbsp; {task_info['rq']}
  </div>
</div>
""", unsafe_allow_html=True)

run_col, trials_col, info_col = st.columns([1.2, 1, 4])
with run_col:
    run_clicked = st.button("▶ Run Benchmark", type="primary", use_container_width=True)
with trials_col:
    st.metric("Trials queued", trials_per_run)
with info_col:
    api_mode = "Live GPT-4o API" if USE_REAL_APIS else "Mock simulation (USE_REAL_APIS=false)"
    st.caption(f"**Task:** {task_info['label']} · **Model:** GPT-4o · **Mode:** {api_mode}")

if run_clicked:
    progress = st.progress(0, text="Running trials...")
    for i in range(trials_per_run):
        seed    = st.session_state.trial_count + i
        trad_r  = MockLLMClient(LLMProvider.GPT4O, protocol="traditional", seed=seed).call(task_key)
        mcp_r   = MockLLMClient(LLMProvider.GPT4O, protocol="mcp",         seed=seed).call(task_key)
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
        progress.progress((i + 1) / trials_per_run,
                          text=f"Trial {st.session_state.trial_count + i + 1} — {task_info['label']}...")
    st.session_state.trial_count += trials_per_run
    progress.empty()
    Path("benchmark/results").mkdir(parents=True, exist_ok=True)
    pd.DataFrame(st.session_state.history).to_csv(
        "benchmark/results/streamlit_results.csv", index=False)
    st.rerun()

# ── Guard: no history yet ──────────────────────────────────────────────────────
if not st.session_state.history:
    st.info("Select a task in the sidebar and click **▶ Run Benchmark** to start.")
    st.stop()

df = pd.DataFrame(st.session_state.history)

# ── Latest trial result cards ──────────────────────────────────────────────────
latest = df.iloc[-1]
lp, rp = st.columns(2)

with lp:
    ok   = bool(latest["trad_success"])
    css  = "result-card" if ok else "result-card fail"
    icon = "✅ Pass" if ok else "❌ Fail"
    st.markdown(f"""
    <div class="{css}">
        <b>Traditional</b> &nbsp;·&nbsp; {icon}<br>
        Tool called: <b>{latest['trad_tool']}</b><br>
        Latency: <b>{latest['trad_latency_ms']:.0f} ms</b> &nbsp;·&nbsp;
        Tool exec: <b>{latest['trad_exec_ms']:.1f} ms</b><br>
        Tokens: <b>{latest['trad_tokens']}</b>
    </div>""", unsafe_allow_html=True)
    if latest.get("_trad_result"):
        with st.expander("Server response (Traditional)"):
            st.code(latest["_trad_result"])

with rp:
    ok   = bool(latest["mcp_success"])
    css  = "result-card" if ok else "result-card fail"
    icon = "✅ Pass" if ok else "❌ Fail"
    st.markdown(f"""
    <div class="{css}">
        <b>MCP</b> &nbsp;·&nbsp; {icon}<br>
        Tool called: <b>{latest['mcp_tool']}</b><br>
        Latency: <b>{latest['mcp_latency_ms']:.0f} ms</b> &nbsp;·&nbsp;
        Tool exec: <b>{latest['mcp_exec_ms']:.1f} ms</b><br>
        Tokens: <b>{latest['mcp_tokens']}</b>
    </div>""", unsafe_allow_html=True)
    if latest.get("_mcp_result"):
        with st.expander("Server response (MCP)"):
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

st.markdown(f'<div class="section-head">Section 3 — Aggregate ({len(df)} trials)</div>',
            unsafe_allow_html=True)
st.markdown("#### Summary Metrics")
st.caption("Six numbers that answer all three research questions at a glance.")

m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Trad Accuracy",  f"{trad_acc:.1f}%")
m2.metric("MCP Accuracy",   f"{mcp_acc:.1f}%",  delta=f"+{mcp_acc - trad_acc:.1f}%")
m3.metric("Trad Latency",   f"{trad_lat:.0f}ms")
m4.metric("MCP Latency",    f"{mcp_lat:.0f}ms",
          delta=f"{mcp_lat - trad_lat:+.0f}ms", delta_color="inverse")
m5.metric("LoC (Legacy)",   f"{loc_trad} lines")
m6.metric("LoC (MCP)",      f"{loc_mcp} lines",  delta=f"-{loc_trad - loc_mcp}", delta_color="normal")
st.caption("RQ3 → Accuracy (m1 vs m2) | RQ2 → Latency (m3 vs m4) | RQ1 → Interoperability LoC (m5 vs m6)")

if USE_REAL_APIS:
    st.markdown("""
<div class="info-banner" style="background:#f0fdf4;border-color:#86efac;color:#166534;">
  ✅ <b>Live GPT-4o data</b> (USE_REAL_APIS=true). Accuracy, latency, and token counts are
  real measurements from the OpenAI API. Each trial above represents one real API call.
  The LoC interoperability metric is verified from actual source code.
</div>""", unsafe_allow_html=True)
else:
    st.markdown("""
<div class="info-banner">
  📊 <b>Mock simulation mode</b> (USE_REAL_APIS=false). Accuracy rates (MCP 94%, Traditional 82%)
  and latency distributions are derived from published OpenAI benchmarks. Token counts are computed
  from real payload content via tiktoken. Set <code>USE_REAL_APIS=true</code> in <code>.env</code>
  for live GPT-4o measurements. The LoC interoperability metric is verified from actual source code.
</div>""", unsafe_allow_html=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — CHARTS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-head">Section 4 — Charts</div>', unsafe_allow_html=True)
st.markdown("#### Visual Analysis")

COLORS = alt.Scale(domain=["Traditional", "MCP"], range=["#ef4444", "#10b981"])

c4a, c4b, c4c = st.columns(3)

with c4a:
    st.markdown("**Latency per Trial (ms)**")
    lat_df = df[["trial", "trad_latency_ms", "mcp_latency_ms"]].melt(
        id_vars="trial", var_name="Protocol", value_name="ms")
    lat_df["Protocol"] = lat_df["Protocol"].map(
        {"trad_latency_ms": "Traditional", "mcp_latency_ms": "MCP"})
    st.altair_chart(
        alt.Chart(lat_df).mark_line(point=True, strokeWidth=2.5).encode(
            x=alt.X("trial:Q", title="Trial #"),
            y=alt.Y("ms:Q", title="ms"),
            color=alt.Color("Protocol:N", scale=COLORS, legend=alt.Legend(orient="top")),
            tooltip=["trial", "Protocol", "ms"],
        ).properties(height=230),
        use_container_width=True)

with c4b:
    st.markdown("**Rolling Accuracy (%)**")
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
        ).properties(height=230),
        use_container_width=True)

with c4c:
    st.markdown("**Avg Token Usage**")
    st.caption("MCP sends full tool manifest (~130 extra prompt tokens per call).")
    tok_df = pd.DataFrame({"Protocol": ["Traditional", "MCP"],
                           "Avg Tokens": [round(trad_tok, 1), round(mcp_tok, 1)]})
    st.altair_chart(
        alt.Chart(tok_df).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
            x=alt.X("Protocol:N", axis=alt.Axis(labelAngle=0), title=None),
            y=alt.Y("Avg Tokens:Q"),
            color=alt.Color("Protocol:N", scale=COLORS, legend=None),
            tooltip=["Protocol", "Avg Tokens"],
        ).properties(height=230),
        use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — STATS + INTEROPERABILITY
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-head">Section 5 — Statistical Analysis and Interoperability</div>',
            unsafe_allow_html=True)

stats_col, _, loc_col = st.columns([5, .3, 4])

with stats_col:
    st.markdown("#### Statistical Significance")
    _MIN = 10
    if len(df) >= _MIN:
        try:
            from scipy import stats as _sp
            tl = df["trad_latency_ms"].tolist()
            ml = df["mcp_latency_ms"].tolist()
            _t, _p = _sp.ttest_ind(ml, tl, equal_var=False)
            _sd1, _sd2 = df["mcp_latency_ms"].std(), df["trad_latency_ms"].std()
            _pooled = math.sqrt((_sd1**2 + _sd2**2) / 2)
            _d = (df["mcp_latency_ms"].mean() - df["trad_latency_ms"].mean()) / _pooled if _pooled else 0
            _, _acc_p = _sp.ttest_ind(
                df["mcp_success"].astype(float).tolist(),
                df["trad_success"].astype(float).tolist(), equal_var=False)
            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Latency p-value", f"{_p:.4f}",
                      delta="sig." if _p < .05 else "not sig.",
                      delta_color="normal" if _p < .05 else "off")
            s2.metric("Cohen's d", f"{_d:.3f}",
                      delta="small" if abs(_d) < .5 else ("medium" if abs(_d) < .8 else "large"),
                      delta_color="off")
            s3.metric("Accuracy p-value", f"{_acc_p:.4f}",
                      delta="sig." if _acc_p < .05 else "not sig.",
                      delta_color="normal" if _acc_p < .05 else "off")
            s4.metric("n trials", len(df))
            if _p < 0.05:
                st.success(
                    f"Latency difference is statistically significant (p={_p:.4f}). "
                    f"Cohen's d = {_d:.3f}.")
            else:
                st.info(f"Not yet significant (p={_p:.4f}). Run more trials (≥ 30 recommended).")
        except ImportError:
            st.warning("Install scipy for significance tests: `pip install scipy`")
    else:
        st.info(f"Run at least {_MIN} trials to unlock statistical testing. ({len(df)}/{_MIN})")

with loc_col:
    st.markdown("#### RQ1 — Interoperability")
    st.caption("Lines of code required to swap AI providers. This is the core MCP claim.")
    lc1, lc2 = st.columns(2)
    with lc1:
        trad_loc = count_loc_to_swap_provider("traditional")
        st.markdown(f"""
        <div class="cmp-card cmp-trad">
            <div class="cmp-label">Traditional</div>
            <div class="cmp-val">{trad_loc['loc_to_swap']}</div>
            <div class="cmp-sub">lines to swap<br>providers</div>
        </div>""", unsafe_allow_html=True)
    with lc2:
        mcp_loc = count_loc_to_swap_provider("mcp")
        st.markdown(f"""
        <div class="cmp-card cmp-mcp">
            <div class="cmp-label">MCP</div>
            <div class="cmp-val">{mcp_loc['loc_to_swap']}</div>
            <div class="cmp-sub">lines to swap<br>providers</div>
        </div>""", unsafe_allow_html=True)
    st.caption(
        "MCP exposes tools via JSON-RPC 2.0. GPT-4o, Gemini, and Claude all connect "
        "identically — zero code changes to swap providers.")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — BENCHMARK HISTORY
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-head">Section 6 — Benchmark History</div>', unsafe_allow_html=True)
st.markdown("#### Trial-by-Trial Results")
st.caption(
    f"**{len(df)} trials** across tasks. "
    "Use **Clear Benchmark History** in the sidebar to start a fresh session."
)

# Summary table
display_cols = ["trial", "task_label", "trad_success", "trad_tool", "trad_latency_ms",
                "mcp_success", "mcp_tool", "mcp_latency_ms"]
display_df = df[display_cols].copy()
display_df.columns = ["Trial", "Task", "Trad Pass", "Trad Tool",
                      "Trad ms", "MCP Pass", "MCP Tool", "MCP ms"]
display_df["Trad ms"] = display_df["Trad ms"].round(0).astype(int)
display_df["MCP ms"]  = display_df["MCP ms"].round(0).astype(int)

with st.expander("Benchmark History Table", expanded=True):
    st.dataframe(display_df, use_container_width=True, height=320)
    st.download_button(
        "⬇ Download CSV",
        df.to_csv(index=False),
        "benchmark_results.csv",
        "text/csv",
        use_container_width=False,
    )

st.caption("Spring 2026 Senior Project  ·  Southwestern College  ·  Joseph Kasongo")
