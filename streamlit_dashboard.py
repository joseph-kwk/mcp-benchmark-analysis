"""
Side-by-Side Benchmark Dashboard
=================================
Streamlit app showing the core comparison:

  LEFT PANE  — "Legacy" traditional function calling
               (tight-coupled, provider-specific, requires restart to swap)

  RIGHT PANE — "MCP" Model Context Protocol
               (decoupled, universal, hot-swap models live)

  BOTTOM     — Live latency and token-usage bar charts updating in real time

Run with:
    streamlit run streamlit_dashboard.py
"""

import time
import random
import sys
import os
from pathlib import Path
import streamlit as st
import pandas as pd
import altair as alt

# Add benchmark dir to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "benchmark"))
from mock_llm import (
    MockLLMClient, LLMProvider,
    make_mcp_claude, make_mcp_gpt4o,
    make_traditional_claude, make_traditional_gpt4o,
    count_loc_to_swap_provider,
)

# Import real server tools directly — server.py functions are plain Python;
# mcp.run() is guarded by if __name__ == '__main__' so this import is safe.
try:
    sys.path.insert(0, os.path.dirname(__file__))
    from server import (
        get_field_status, get_weather_forecast, recommend_irrigation,
        activate_irrigation, log_sensor_reading, get_crop_schedule,
        calculate_area,
    )
    _SERVER_AVAILABLE = True
except Exception as _e:
    _SERVER_AVAILABLE = False
    _SERVER_ERROR = str(_e)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MCP Benchmark Dashboard",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .metric-container { background: #f8f9fa; border-radius: 8px; padding: 12px; margin-bottom: 8px; }
    .mcp-badge   { background: #d1fae5; color: #065f46; padding: 3px 10px; border-radius: 12px; font-size: 0.82em; font-weight: 600; }
    .trad-badge  { background: #fee2e2; color: #991b1b; padding: 3px 10px; border-radius: 12px; font-size: 0.82em; font-weight: 600; }
    .result-box  { background: #f1f5f9; border-left: 4px solid #6366f1; border-radius: 4px; padding: 10px 14px; font-family: monospace; font-size: 0.88em; color: #1e293b; }
    .result-fail { border-left-color: #ef4444; background: #fff5f5; color: #1e293b; }
    .header-row  { display: flex; align-items: center; gap: 10px; }
    .field-card  { border-radius: 10px; padding: 16px; text-align: center; color: white; font-weight: 600; }
    .field-healthy  { background: linear-gradient(135deg, #10b981, #34d399); }
    .field-warning  { background: linear-gradient(135deg, #f59e0b, #fbbf24); }
    .field-critical { background: linear-gradient(135deg, #ef4444, #f87171); }
    .field-moisture { font-size: 2em; font-weight: 700; margin: 6px 0; }
    .flow-box { background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 8px;
                padding: 10px 18px; font-family: monospace; font-size: 0.88em;
                text-align: center; color: #374151; }
</style>
""", unsafe_allow_html=True)

# ── Live field state (simulated digital twin moisture decay) ───────────────────
if "fields" not in st.session_state:
    st.session_state.fields = {
        "Field A": {"crop": "Corn",    "moisture": 12.0, "base": 12.0},
        "Field B": {"crop": "Wheat",   "moisture": 28.0, "base": 28.0},
        "Field C": {"crop": "Soybean", "moisture":  8.0, "base":  8.0},
        "Field D": {"crop": "Corn",    "moisture": 45.0, "base": 45.0},
    }
if "sim_ticks" not in st.session_state:
    st.session_state.sim_ticks = 0

# ── Session state init ─────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []          # list of trial dicts
if "trial_count" not in st.session_state:
    st.session_state.trial_count = 0
if "mcp_model" not in st.session_state:
    st.session_state.mcp_model = "claude_3.5"
if "trad_model" not in st.session_state:
    st.session_state.trad_model = "claude_3.5"

if "last_server_response" not in st.session_state:
    st.session_state.last_server_response = None

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Configuration")

    st.subheader("Right Pane — MCP")
    mcp_model = st.selectbox(
        "MCP Model (hot-swap, no restart)",
        ["claude_3.5", "gpt4o"],
        key="mcp_model_select",
        help="MCP server is provider-agnostic. Swap freely.",
    )

    st.divider()

    st.subheader("Left Pane — Traditional")
    trad_model_display = st.selectbox(
        "Traditional Model (⚠ requires code restart)",
        ["claude_3.5", "gpt4o"],
        key="trad_model_select",
        disabled=False,
        help="In real legacy code, swapping this requires schema rewrites and restart.",
    )
    loc_data = count_loc_to_swap_provider("traditional")
    st.warning(f"⚠️ Swapping this model would require **{loc_data['loc_to_swap']} lines changed** in production code.")

    st.divider()

    task_choice = st.selectbox(
        "Task to benchmark",
        ["irrigation_check", "field_status", "weather_forecast",
         "recommend_action", "log_sensor", "crop_schedule", "pump_stop"],
        help="The farm task you want the LLM to execute."
    )

    trials_per_run = st.slider("Trials per run", 1, 50, 10)

    st.divider()
    if st.button("🗑️ Clear History"):
        st.session_state.history = []
        st.session_state.trial_count = 0
        st.rerun()

    st.caption("API keys not required. Switch `USE_REAL_APIS=true` + set env vars when ready.")

    st.divider()
    st.subheader("📖 How to Use")
    st.markdown("""
**Step 1 — Digital Twin** *(top of page)*  
See the live farm. Click **Simulate Tick** to drain moisture.  
Click **🔄 Fetch from Server** to pull real data from `server.py`.  
Fields A & C below 20 % show a **💧 Irrigate** button — click it to see the pump API key vault in action.

---
**Step 2 — Run Benchmark** *(middle of page)*  
Pick a **Task** and **Trials** in this sidebar, then hit **▶ Run Benchmark**.  
Left pane = Traditional (provider-locked).  
Right pane = MCP (provider-agnostic).  
Each card shows the real server response + execution time.

---
**Step 3 — Read the Metrics** *(below benchmark)*  
• 🎯 **Accuracy** → did the LLM pick the right tool?  
• ⏱ **Latency** → total round-trip incl. tool execution  
• 🔌 **Interoperability** → lines of code to swap provider  
• 🔬 **Stats** → unlocks after 10 trials (p-value, Cohen's d)

---
**Step 4 — Swap the MCP Model** *(this sidebar)*  
Change **MCP Model** dropdown and re-run — *zero code changes*.  
Compare vs the Traditional side that would need {47} lines rewritten.

---
**Step 5 — Download Results**  
Scroll to **Raw Trial Data** → **⬇ Download CSV**.
    """)

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("🌾 MCP Benchmark Dashboard")
st.caption("**Benchmarking the Model Context Protocol** — Interoperability, Latency, and Accuracy · Spring 2026 Senior Project · Southwestern College")

# ── Orientation banner ─────────────────────────────────────────────────────────
with st.expander("🗺️ Dashboard Tour — click to see what each section does", expanded=False):
    t1, t2, t3 = st.columns(3)
    with t1:
        st.markdown("""**🌱 Step 1 · Digital Twin**  
A simulated farm with 4 fields. Moisture drains over time.  
→ Shows **why** LLMs need tool-calling (a real pump must fire).  
→ Click **Fetch from Server** to call `get_field_status()` live.  
→ Click **💧 Irrigate** to fire `activate_irrigation()` and see the key vault response in JSON.
""")
    with t2:
        st.markdown("""**📊 Step 2 · Benchmark**  
Run N trials of the same task through both protocols.  
→ **Accuracy**: did the LLM call the right tool with right args?  
→ **Latency**: end-to-end ms including real tool execution  
→ **Interoperability**: 0 LoC (MCP) vs 47 LoC (Traditional) to swap AI provider  
→ After 10+ trials: p-value + Cohen's d unlock automatically.
""")
    with t3:
        st.markdown("""**🔬 Step 3 · Research Questions**  
This dashboard answers 3 RQs:  
→ **RQ1** Interoperability — scroll to the 🔌 section  
→ **RQ2** Latency overhead — see the ⏱ line chart + stats panel  
→ **RQ3** Accuracy — see the 🎯 rolling accuracy chart  

Download all trial data: **Raw Trial Data → ⬇ CSV**  
Full 100-trial results live in `benchmark/results/`.
""")
    st.info("💡 Tip: use the sidebar to pick task type, model, and trials per run. MCP model can be swapped live — Traditional cannot.")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — DIGITAL TWIN  (the "why this matters" context)
# ─────────────────────────────────────────────────────────────────────────────
with st.expander("🌱 Step 1 — The Digital Twin: Smart Farm Simulation", expanded=True):
    st.caption(
        "A virtual farm where soil moisture drains over time. "
        "When moisture drops low, the LLM must call `activate_irrigation`. "
        "This is what we're benchmarking. Click **Simulate Tick** to watch moisture drain."
    )

    if not _SERVER_AVAILABLE:
        st.error(f"⚠️ server.py not importable: {_SERVER_ERROR}")

    # Simulate one moisture-decay tick
    tick_col, reset_col, refresh_col, _ = st.columns([1, 1, 1.5, 3])
    with tick_col:
        if st.button("▶ Simulate Tick", use_container_width=True):
            for f in st.session_state.fields.values():
                f["moisture"] = max(3.0, f["moisture"] - random.uniform(0.5, 1.5))
            st.session_state.sim_ticks += 1
    with reset_col:
        if st.button("↺ Reset", use_container_width=True):
            for name, f in st.session_state.fields.items():
                f["moisture"] = f["base"]
            st.session_state.sim_ticks = 0
            st.session_state.last_server_response = None
    with refresh_col:
        if st.button("🔄 Fetch from Server", use_container_width=True, help="Call get_field_status() on the real server.py for each field"):
            if _SERVER_AVAILABLE:
                s = time.perf_counter()
                responses = {}
                for fid in ["Field_A", "Field_B", "Field_C", "Field_D"]:
                    responses[fid] = get_field_status(fid)
                elapsed = (time.perf_counter() - s) * 1000
                # Sync Streamlit moisture state with real server values
                _key_map = {"Field_A": "Field A", "Field_B": "Field B",
                             "Field_C": "Field C", "Field_D": "Field D"}
                for fid, resp in responses.items():
                    if "moisture_pct" in resp:
                        st.session_state.fields[_key_map[fid]]["moisture"] = float(resp["moisture_pct"])
                st.session_state.last_server_response = {
                    "source": "server.get_field_status()",
                    "elapsed_ms": round(elapsed, 3),
                    "responses": responses,
                }
            else:
                st.error("server.py not available")

    st.caption(f"Simulation ticks: **{st.session_state.sim_ticks}** (each tick ≈ 1 hour of evaporation)")

    # Field cards  +  per-field irrigation button
    fcols = st.columns(4)
    field_items = list(st.session_state.fields.items())
    for i, (fname, fdata) in enumerate(field_items):
        m = fdata["moisture"]
        css    = "field-critical" if m < 10 else ("field-warning" if m < 20 else "field-healthy")
        status = "🔴 CRITICAL"  if m < 10 else ("🟡 Needs Water" if m < 20 else "🟢 Healthy")
        # Map display name → server field ID
        fid_map = {"Field A": "Field_A", "Field B": "Field_B",
                    "Field C": "Field_C", "Field D": "Field_D"}
        fid = fid_map[fname]
        with fcols[i]:
            st.markdown(f"""
            <div class="field-card {css}">
                <div>{fname}</div>
                <div class="field-moisture">{m:.0f}%</div>
                <div style="font-size:0.8em">{fdata['crop']}</div>
                <div style="font-size:0.78em; margin-top:4px; opacity:0.9">{status}</div>
            </div>
            """, unsafe_allow_html=True)
            # Show irrigation button only for fields that need water
            if m < 20 and _SERVER_AVAILABLE:
                if st.button(f"💧 Irrigate {fname}", key=f"irr_{fname}", use_container_width=True):
                    s = time.perf_counter()
                    result = activate_irrigation(fid, "start", 30)
                    elapsed = (time.perf_counter() - s) * 1000
                    st.session_state.last_server_response = {
                        "source": f"server.activate_irrigation('{fid}', 'start', 30)",
                        "elapsed_ms": round(elapsed, 3),
                        "responses": {fid: result},
                    }
                    # Boost moisture after irrigation
                    if result.get("success"):
                        fdata["moisture"] = min(fdata["moisture"] + 20, 60.0)

    # Real server response viewer
    if st.session_state.last_server_response:
        resp_data = st.session_state.last_server_response
        st.divider()
        st.markdown(f"""
        <div style="background:#f0fdf4; border-left:4px solid #10b981; border-radius:6px;
                    padding:10px 14px; font-family:monospace; font-size:0.82em;">
            ✅ <b>Real server.py response</b> —
            <code>{resp_data['source']}</code>
            &nbsp;&nbsp;|  ⏱ <b>{resp_data['elapsed_ms']} ms</b>
        </div>
        """, unsafe_allow_html=True)
        import json as _json
        with st.expander("📦 Full server response (raw JSON)"):
            st.code(_json.dumps(resp_data["responses"], indent=2), language="json")

    st.divider()

    # MCP data flow diagram
    st.caption("**How this data flows — the MCP architecture:**")
    fc1, fc2, fc3, fc4, fc5 = st.columns([2, 0.5, 2, 0.5, 2])
    with fc1:
        st.markdown('<div class="flow-box">🌡️ Digital Twin<br/><small>Soil sensor data</small></div>', unsafe_allow_html=True)
    with fc2:
        st.markdown("<div style='text-align:center; padding-top:14px; color:#6366f1; font-weight:700'>→</div>", unsafe_allow_html=True)
    with fc3:
        st.markdown('<div class="flow-box">🔧 FastMCP Server<br/><small>activate_irrigation()<br/>Key vault: never exposed</small></div>', unsafe_allow_html=True)
    with fc4:
        st.markdown("<div style='text-align:center; padding-top:14px; color:#6366f1; font-weight:700'>→</div>", unsafe_allow_html=True)
    with fc5:
        st.markdown('<div class="flow-box">🤖 LLM (Claude / GPT-4o)<br/><small>Decides which tool to call<br/>via JSON-RPC 2.0</small></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — BENCHMARK COMPARISON  (the actual research)
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("📊 Step 2 — The Benchmark: MCP vs Traditional")

col_left_hdr, col_right_hdr = st.columns(2)
with col_left_hdr:
    st.markdown('<span class="trad-badge">⚠ Traditional Function Calling (Legacy)</span>', unsafe_allow_html=True)
    st.caption("Tight-coupled • Provider-specific schema • Key in app layer • Restart to swap model")
with col_right_hdr:
    st.markdown('<span class="mcp-badge">✅ MCP — Model Context Protocol</span>', unsafe_allow_html=True)
    st.caption("Decoupled • Universal JSON-RPC 2.0 • Key stays on server • Hot-swap models live")

st.divider()

# ── Run benchmark button ────────────────────────────────────────────────────────
run_col, info_col = st.columns([1, 3])
with run_col:
    run_clicked = st.button("▶ Run Benchmark", type="primary", use_container_width=True)
with info_col:
    st.caption(f"Task: **{task_choice}** | Trials: **{trials_per_run}** | "
               f"Traditional: **{trad_model_display}** | MCP: **{mcp_model}**")

# ── Execute trials ─────────────────────────────────────────────────────────────
if run_clicked:
    trad_provider = LLMProvider.CLAUDE_35 if "claude" in trad_model_display else LLMProvider.GPT4O
    mcp_provider  = LLMProvider.CLAUDE_35 if "claude" in mcp_model else LLMProvider.GPT4O

    progress = st.progress(0, text="Running trials...")

    for i in range(trials_per_run):
        seed = st.session_state.trial_count + i

        trad_client = MockLLMClient(trad_provider, protocol="traditional", seed=seed)
        mcp_client  = MockLLMClient(mcp_provider,  protocol="mcp",         seed=seed)

        trad_resp = trad_client.call(task_choice)
        mcp_resp  = mcp_client.call(task_choice)

        st.session_state.history.append({
            "trial":            st.session_state.trial_count + i + 1,
            "task":             task_choice,
            # Traditional
            "trad_model":       trad_model_display,
            "trad_latency_ms":  trad_resp.latency_ms,
            "trad_tokens":      trad_resp.prompt_tokens + trad_resp.completion_tokens,
            "trad_success":     trad_resp.success,
            "trad_tool":        trad_resp.tool_called,
            "trad_exec_ms":     trad_resp.tool_exec_ms,
            # MCP
            "mcp_model":        mcp_model,
            "mcp_latency_ms":   mcp_resp.latency_ms,
            "mcp_tokens":       mcp_resp.prompt_tokens + mcp_resp.completion_tokens,
            "mcp_success":      mcp_resp.success,
            "mcp_tool":         mcp_resp.tool_called,
            "mcp_exec_ms":      mcp_resp.tool_exec_ms,
            # Last real server response (for display only, not charted)
            "_trad_result":     str(trad_resp.tool_result) if trad_resp.tool_result else None,
            "_mcp_result":      str(mcp_resp.tool_result)  if mcp_resp.tool_result  else None,
        })
        progress.progress((i + 1) / trials_per_run, text=f"Trial {i+1}/{trials_per_run}...")

    st.session_state.trial_count += trials_per_run
    progress.empty()

    # Auto-save results to benchmark/results/ after every run
    _results_dir = Path("benchmark/results")
    _results_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(st.session_state.history).to_csv(
        _results_dir / "streamlit_results.csv", index=False
    )

    st.rerun()

# ── Display results ────────────────────────────────────────────────────────────
if not st.session_state.history:
    st.info("👆 Configure a task in the sidebar and click **Run Benchmark** to start.")
    st.stop()

df = pd.DataFrame(st.session_state.history)

# ── Latest trial side-by-side ──────────────────────────────────────────────────
latest = df.iloc[-1]
left_pane, right_pane = st.columns(2)

with left_pane:
    st.subheader("Traditional — Last Result")
    status_icon = "✅" if latest["trad_success"] else "❌"
    css_class = "result-box" if latest["trad_success"] else "result-box result-fail"
    st.markdown(f"""
    <div class="{css_class}">
        {status_icon} Tool called: <b>{latest['trad_tool']}</b><br>
        ⏱ Total latency: <b>{latest['trad_latency_ms']:.0f} ms</b><br>
        🔧 Tool exec: <b>{latest['trad_exec_ms']:.2f} ms</b><br>
        🪙 Tokens: <b>{latest['trad_tokens']}</b><br>
        🤖 Model: <b>{latest['trad_model']}</b>
    </div>
    """, unsafe_allow_html=True)
    if latest.get("_trad_result"):
        with st.expander("📦 Server response (Traditional path)"):
            st.code(latest["_trad_result"], language="json")

with right_pane:
    st.subheader("MCP — Last Result")
    status_icon = "✅" if latest["mcp_success"] else "❌"
    css_class = "result-box" if latest["mcp_success"] else "result-box result-fail"
    st.markdown(f"""
    <div class="{css_class}">
        {status_icon} Tool called: <b>{latest['mcp_tool']}</b><br>
        ⏱ Total latency: <b>{latest['mcp_latency_ms']:.0f} ms</b><br>
        🔧 Tool exec: <b>{latest['mcp_exec_ms']:.2f} ms</b><br>
        🪙 Tokens: <b>{latest['mcp_tokens']}</b><br>
        🤖 Model: <b>{latest['mcp_model']}</b>
    </div>
    """, unsafe_allow_html=True)
    if latest.get("_mcp_result"):
        with st.expander("📦 Server response (MCP path)"):
            st.code(latest["_mcp_result"], language="json")

st.divider()

# ── Aggregate metrics ──────────────────────────────────────────────────────────
st.subheader(f"📊 Aggregate Results — {len(df)} trials")
st.caption("These six numbers answer all three research questions at a glance.")
m1, m2, m3, m4, m5, m6 = st.columns(6)

trad_acc = df["trad_success"].mean() * 100
mcp_acc  = df["mcp_success"].mean()  * 100
trad_lat = df["trad_latency_ms"].mean()
mcp_lat  = df["mcp_latency_ms"].mean()
trad_tok = df["trad_tokens"].mean()
mcp_tok  = df["mcp_tokens"].mean()

loc_mcp  = count_loc_to_swap_provider("mcp")["loc_to_swap"]
loc_trad = count_loc_to_swap_provider("traditional")["loc_to_swap"]

m1.metric("Traditional Accuracy",  f"{trad_acc:.1f}%")
m2.metric("MCP Accuracy",          f"{mcp_acc:.1f}%",  delta=f"+{mcp_acc - trad_acc:.1f}%")
m3.metric("Traditional Latency",   f"{trad_lat:.0f}ms")
m4.metric("MCP Latency",           f"{mcp_lat:.0f}ms",  delta=f"{mcp_lat - trad_lat:+.0f}ms", delta_color="inverse")
m5.metric("LoC to swap (Legacy)",  f"{loc_trad} lines")
m6.metric("LoC to swap (MCP)",     f"{loc_mcp} lines",  delta=f"-{loc_trad - loc_mcp} lines")
st.caption("🎯 Accuracy (m1 vs m2) → **RQ3**  \u00a0|   ⏱ Latency (m3 vs m4) → **RQ2**  \u00a0|   🔌 LoC to swap (m5 vs m6) → **RQ1**")

st.divider()

# ── Live charts ────────────────────────────────────────────────────────────────
chart_col1, chart_col2 = st.columns(2)

# Latency over time
with chart_col1:
    st.subheader("⏱ Latency Per Trial (ms)")
    latency_df = df[["trial", "trad_latency_ms", "mcp_latency_ms"]].melt(
        id_vars="trial",
        value_vars=["trad_latency_ms", "mcp_latency_ms"],
        var_name="Protocol",
        value_name="Latency (ms)"
    )
    latency_df["Protocol"] = latency_df["Protocol"].map({
        "trad_latency_ms": "Traditional",
        "mcp_latency_ms":  "MCP"
    })
    chart = alt.Chart(latency_df).mark_line(point=True).encode(
        x=alt.X("trial:Q", title="Trial #"),
        y=alt.Y("Latency (ms):Q", title="Latency (ms)"),
        color=alt.Color("Protocol:N", scale=alt.Scale(
            domain=["Traditional", "MCP"],
            range=["#ef4444", "#10b981"]
        )),
        tooltip=["trial", "Protocol", "Latency (ms)"]
    ).properties(height=280)
    st.altair_chart(chart, use_container_width=True)

# Accuracy comparison
with chart_col2:
    st.subheader("🎯 Accuracy Rate (Rolling)")
    # Rolling 10-trial accuracy
    window = min(10, len(df))
    acc_df = pd.DataFrame({
        "trial":       df["trial"],
        "Traditional": df["trad_success"].rolling(window, min_periods=1).mean() * 100,
        "MCP":         df["mcp_success"].rolling(window, min_periods=1).mean()  * 100,
    }).melt(id_vars="trial", var_name="Protocol", value_name="Accuracy (%)")

    chart2 = alt.Chart(acc_df).mark_line(point=True).encode(
        x=alt.X("trial:Q",        title="Trial #"),
        y=alt.Y("Accuracy (%):Q", title="Accuracy (%)", scale=alt.Scale(domain=[50, 105])),
        color=alt.Color("Protocol:N", scale=alt.Scale(
            domain=["Traditional", "MCP"],
            range=["#ef4444", "#10b981"]
        )),
        tooltip=["trial", "Protocol", "Accuracy (%)"]
    ).properties(height=280)
    st.altair_chart(chart2, use_container_width=True)

# Token comparison bar chart
st.subheader("🪙 Token Usage Comparison")
tok_data = pd.DataFrame({
    "Protocol": ["Traditional", "MCP"],
    "Avg Tokens": [trad_tok, mcp_tok],
})
tok_chart = alt.Chart(tok_data).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
    x=alt.X("Protocol:N", axis=alt.Axis(labelAngle=0)),
    y=alt.Y("Avg Tokens:Q"),
    color=alt.Color("Protocol:N", scale=alt.Scale(
        domain=["Traditional", "MCP"],
        range=["#ef4444", "#10b981"]
    ), legend=None),
    tooltip=["Protocol", "Avg Tokens"]
).properties(height=200)
st.altair_chart(tok_chart, use_container_width=True)

st.divider()

# ── Statistical significance (shown once we have enough trials) ─────────────────
_MIN_TRIALS_FOR_STATS = 10
if len(df) >= _MIN_TRIALS_FOR_STATS:
    st.subheader("🔬 Statistical Significance")
    try:
        from scipy import stats as _sp
        import math as _math
        _trad_lat = df["trad_latency_ms"].tolist()
        _mcp_lat  = df["mcp_latency_ms"].tolist()
        _t, _p    = _sp.ttest_ind(_mcp_lat, _trad_lat, equal_var=False)
        _n1, _n2  = len(_mcp_lat), len(_trad_lat)
        _sd1, _sd2 = df["mcp_latency_ms"].std(), df["trad_latency_ms"].std()
        _pooled   = _math.sqrt((_sd1**2 + _sd2**2) / 2)
        _d        = (df["mcp_latency_ms"].mean() - df["trad_latency_ms"].mean()) / _pooled if _pooled else 0
        _sig      = _p < 0.05
        _acc_t, _acc_p = _sp.ttest_ind(
            df["mcp_success"].astype(float).tolist(),
            df["trad_success"].astype(float).tolist(),
            equal_var=False
        )
        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("Latency p-value",  f"{_p:.4f}", delta="Significant" if _sig else "Not sig.",
                   delta_color="normal" if _sig else "off")
        sc2.metric("Cohen's d (latency)", f"{_d:.3f}",
                   delta="small" if abs(_d) < 0.5 else ("medium" if abs(_d) < 0.8 else "large"),
                   delta_color="off")
        sc3.metric("Accuracy p-value", f"{_acc_p:.4f}",
                   delta="Significant" if _acc_p < 0.05 else "Not sig.",
                   delta_color="normal" if _acc_p < 0.05 else "off")
        sc4.metric("Trials analysed", len(df))
        if _sig:
            st.success(f"✅ The latency difference is **statistically significant** (p={_p:.4f} < 0.05). "
                       f"Cohen\u2019s d = {_d:.3f} — {'small' if abs(_d)<0.5 else ('medium' if abs(_d)<0.8 else 'large')} effect.")
        else:
            st.info(f"ℹ️ Latency difference is **not yet significant** (p={_p:.4f}). Run more trials.")
    except ImportError:
        st.warning("scipy not installed — run `pip install scipy` for significance tests.")
else:
    st.info(f"🔬 Run at least {_MIN_TRIALS_FOR_STATS} trials to unlock statistical significance testing.")

st.divider()

# ── Interoperability explainer ────────────────────────────────────────────────
st.subheader("🔌 Interoperability — The USB-C Argument")
exp_col1, exp_col2 = st.columns(2)
with exp_col1:
    trad_loc = count_loc_to_swap_provider("traditional")
    st.error(f"**Traditional — {trad_loc['loc_to_swap']} lines to swap providers**")
    for f in trad_loc["changed_files"]:
        st.caption(f"• {f}")
    st.caption(trad_loc["explanation"])
with exp_col2:
    mcp_loc = count_loc_to_swap_provider("mcp")
    st.success(f"**MCP — {mcp_loc['loc_to_swap']} lines to swap providers**")
    st.caption(mcp_loc["explanation"])
    st.caption("Claude → GPT-4o → Gemini: same server, same tools, zero changes.")

st.divider()

# ── Raw data table ────────────────────────────────────────────────────────────
with st.expander("📋 Raw Trial Data"):
    st.dataframe(df, use_container_width=True)
    csv = df.to_csv(index=False)
    st.download_button("⬇ Download CSV", csv, "benchmark_results.csv", "text/csv")

st.caption("Spring 2026 Senior Project • Southwestern College • Joseph Kasongo")
