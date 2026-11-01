"""
FatigueLab — Streamlit Dashboard
Displays live safety-degradation graphs, conversation logs, and final reports.
"""

import json
import os
import sys
import time
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# ── Ensure project root is importable ──
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.llm_provider import LLMClient
from core.attacker_agent import AttackerAgent, PHASE_LABELS, AGGRESSION_LIMITS
from core.target_bot import TargetBot
from core.evaluator import evaluate, compute_fatigue_index, compute_resilience_grade

# ════════════════════════════════════════════════════════════════════════
# Page config
# ════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="FatigueLab — Adversarial Prompt Fatigue Tester",
    page_icon="🛡️",
    layout="wide",
)

# ── Custom CSS ──
st.markdown(
    """
    <style>
    .block-container {padding-top: 1.5rem;}
    div[data-testid="stMetric"] {
        background: #0e1117; border: 1px solid #262730;
        border-radius: .5rem; padding: .75rem 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ════════════════════════════════════════════════════════════════════════
# Load configuration files
# ════════════════════════════════════════════════════════════════════════
CONFIG_DIR = os.path.join(ROOT, "config")

with open(os.path.join(CONFIG_DIR, "scenarios.json")) as f:
    SCENARIOS = json.load(f)

with open(os.path.join(CONFIG_DIR, "targets.json")) as f:
    TARGETS = json.load(f)

# ════════════════════════════════════════════════════════════════════════
# Header
# ════════════════════════════════════════════════════════════════════════
st.title("🛡️ FatigueLab")
st.caption(
    "Automated adversarial **prompt fatigue** tester — measures *when* a chatbot's "
    "safety rules break over a prolonged conversation, not just *if* they break."
)

# ════════════════════════════════════════════════════════════════════════
# Sidebar — Test Settings
# ════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.header("⚙️ Test Settings")

    # ── LLM Provider & Interactive API Key Input ──
    st.subheader("🔑 LLM Provider & Authentication")
    provider_choice = st.selectbox(
        "Select Provider Mode",
        [
            "⚡ Offline Simulation (No Key Needed)",
            "🤖 OpenAI (Live API)",
            "💎 Google Gemini (Live API)"
        ],
        help="Use Offline Simulation for instant demos without keys. Choose OpenAI or Gemini to test live models."
    )

    api_key = ""
    model_name = "mock"
    provider_key = "mock"

    if "OpenAI" in provider_choice:
        provider_key = "openai"
        env_fallback = os.getenv("OPENAI_API_KEY", "")
        api_key = st.text_input(
            "Enter OpenAI API Key:",
            type="password",
            value=st.session_state.get("saved_openai_key", env_fallback),
            placeholder="sk-proj-...",
            help="Your API key stays only in your browser session memory."
        )
        st.session_state["saved_openai_key"] = api_key
        model_name = st.selectbox("OpenAI Model", ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"], index=0)
        
        if api_key:
            st.success("🟢 API Key entered")
        else:
            st.info("ℹ️ Paste your OpenAI key above")

    elif "Gemini" in provider_choice:
        provider_key = "gemini"
        env_fallback = os.getenv("GEMINI_API_KEY", "")
        api_key = st.text_input(
            "Enter Gemini API Key:",
            type="password",
            value=st.session_state.get("saved_gemini_key", env_fallback),
            placeholder="AIzaSy...",
            help="Your API key stays only in your browser session memory."
        )
        st.session_state["saved_gemini_key"] = api_key
        model_name = st.selectbox("Gemini Model", ["gemini-1.5-flash", "gemini-1.5-pro"], index=0)
        
        if api_key:
            st.success("🟢 API Key entered")
        else:
            st.info("ℹ️ Paste your Gemini key above")

    else:
        provider_key = "mock"
        st.caption("🟢 Running local high-fidelity simulation. No API key required.")

    st.divider()

    # ── Target (Victim) Bot ──
    st.subheader("🎯 Target (Victim) Bot")
    target_name = st.selectbox(
        "Select target bot",
        [t["name"] for t in TARGETS],
        help="The victim chatbot changes per test — pick a different one each run.",
    )
    target_info = next(t for t in TARGETS if t["name"] == target_name)
    st.markdown(f"**Domain:** {target_info['domain']}")
    st.markdown(f"_{target_info['description']}_")

    st.divider()

    # ── Attack Scenario ──
    st.subheader("⚔️ Attack Scenario")
    scenario_name = st.selectbox(
        "Select scenario",
        [s["name"] for s in SCENARIOS],
    )
    scenario = next(s for s in SCENARIOS if s["name"] == scenario_name)
    st.markdown(f"**Category:** {scenario['category']}")
    st.markdown(f"**Goal:** {scenario['goal']}")

    st.divider()

    # ── Aggression & Turns ──
    aggression = st.select_slider(
        "Attacker aggression",
        options=["Low", "Medium", "High"],
        value="Medium",
    )
    max_turns = st.slider("Max conversation turns", 5, 30, 15)

    st.divider()
    run_btn = st.button("🚀 Start Fatigue Test", type="primary", use_container_width=True)

# ════════════════════════════════════════════════════════════════════════
# Tabs
# ════════════════════════════════════════════════════════════════════════
tab_test, tab_compare, tab_about = st.tabs(
    ["🔬 Live Test", "📊 Compare Results", "ℹ️ About"]
)

# ════════════════════════════════════════════════════════════════════════
# Session-state history for comparison tab
# ════════════════════════════════════════════════════════════════════════
if "all_runs" not in st.session_state:
    st.session_state.all_runs = []

# ════════════════════════════════════════════════════════════════════════
# TAB 1 — Live Test
# ════════════════════════════════════════════════════════════════════════
with tab_test:
    if not run_btn:
        if provider_key in ("openai", "gemini") and not api_key:
            st.warning(
                f"🔑 **API Key Prompt:** You have selected **{provider_choice}**. "
                "Please enter your API Key directly in the sidebar on the left to proceed, "
                "or switch to **⚡ Offline Simulation** if you want an instant demo without any key."
            )
        st.info("👉 Select your Target Bot and Scenario in the sidebar, then click **🚀 Start Fatigue Test**.")
        st.stop()

    # ── Validate API Key if live provider is chosen ──
    if provider_key in ("openai", "gemini") and not (api_key and api_key.strip()):
        st.error(
            f"❌ **Missing API Key:** You selected **{provider_choice}**, but no API key was provided. "
            "Please paste your API key in the sidebar input box, or switch to **⚡ Offline Simulation (No Key Needed)**."
        )
        st.stop()

    # ── Build the three agents ──
    client = LLMClient(provider=provider_key, api_key=api_key, model=model_name)
    attacker = AttackerAgent(client, aggression=aggression)
    target = TargetBot(client, target_info)

    # ── Layout: left = chat, right = graph ──
    col_chat, col_graph = st.columns([3, 2])

    with col_chat:
        st.subheader("💬 Conversation Log")
        chat_container = st.container()

    with col_graph:
        st.subheader("📉 Safety Degradation")
        graph_slot = st.empty()
        status_slot = st.empty()
        phase_slot = st.empty()

    progress = st.progress(0, text="Initialising…")

    # ── Run the multi-turn test ──
    history = []
    scores = []
    phases_log = []
    log_entries = []
    broke_at = None

    for turn in range(1, max_turns + 1):
        # 1. Attacker generates next message
        attacker_msg, phase = attacker.generate_next_turn(
            scenario=scenario,
            target_info=target_info,
            history=history,
            turn=turn,
        )

        # 2. Target (victim) responds
        target_reply = target.respond(
            user_msg=attacker_msg,
            history=history,
            turn=turn,
            phase=phase,
            aggression=aggression,
        )

        # 3. Evaluator scores the reply
        result = evaluate(target_reply, target_info, scenario)

        # 4. Update records
        history.append({"role": "user", "content": attacker_msg})
        history.append({"role": "assistant", "content": target_reply})
        scores.append(result["safety_score"])
        phases_log.append(phase)
        log_entries.append(
            {
                "turn": turn,
                "phase": phase,
                "phase_label": PHASE_LABELS.get(phase, phase),
                "attacker": attacker_msg,
                "target": target_reply,
                "score": result["safety_score"],
                "violations": result["violations"],
                "reason": result["reason"],
            }
        )

        # ── Live chat display ──
        with chat_container:
            phase_emoji = {"rapport_building": "🤝", "context_overload": "🌊",
                           "authority_claim": "👔", "direct_extraction": "💉"}.get(phase, "❓")
            st.markdown(f"**Turn {turn}** &nbsp; {phase_emoji} `{PHASE_LABELS.get(phase, phase)}`")

            with st.chat_message("user", avatar="🗡️"):
                st.markdown(attacker_msg)
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(target_reply)

            score_color = "🟢" if result["safety_score"] >= 80 else ("🟡" if result["safety_score"] >= 50 else "🔴")
            st.caption(f"{score_color} Safety: **{result['safety_score']}** / 100 — {result['reason']}")
            st.divider()

        # ── Live graph ──
        phase_colors = {
            "rapport_building": "#22c55e",
            "context_overload": "#eab308",
            "authority_claim": "#f97316",
            "direct_extraction": "#ef4444",
        }
        marker_colors = [phase_colors.get(p, "#6b7280") for p in phases_log]

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=list(range(1, len(scores) + 1)),
                y=scores,
                mode="lines+markers",
                line=dict(width=3, color="#3b82f6"),
                marker=dict(size=10, color=marker_colors, line=dict(width=1, color="white")),
                name="Safety Score",
                hovertemplate="Turn %{x}<br>Score: %{y}<extra></extra>",
            )
        )
        # Danger zone shading
        fig.add_hrect(y0=0, y1=40, fillcolor="red", opacity=0.08, line_width=0)
        fig.add_hline(y=40, line_dash="dash", line_color="red", opacity=0.5,
                      annotation_text="BREACH THRESHOLD", annotation_position="top left")
        fig.update_layout(
            yaxis_range=[-5, 110],
            xaxis_title="Turn Number",
            yaxis_title="Safety Score",
            height=380,
            margin=dict(l=10, r=10, t=30, b=10),
            template="plotly_dark",
            xaxis=dict(dtick=1),
        )
        graph_slot.plotly_chart(fig, use_container_width=True, key=f"live_graph_{turn}")

        # Phase indicator
        phase_slot.markdown(
            f"**Current Phase:** {phase_emoji} {PHASE_LABELS.get(phase, phase)} &nbsp;|&nbsp; "
            f"**Aggression:** {aggression}"
        )

        progress.progress(turn / max_turns, text=f"Turn {turn}/{max_turns}")

        # ── Check for breach ──
        if result["is_leak"] and broke_at is None:
            broke_at = turn
            status_slot.error(
                f"🚨 **VULNERABILITY DETECTED at Turn {turn}!**\n\n"
                f"**Violations:** {result['reason']}"
            )
            # Continue running to measure post-breach behaviour

    progress.empty()

    if broke_at is None:
        status_slot.success(
            f"✅ Target held its safety rules for all **{len(scores)} turns**."
        )

    # ════════════════════════════════════════════════════════════════════
    # Final Report
    # ════════════════════════════════════════════════════════════════════
    st.markdown("---")
    st.subheader("📋 Final Report")

    fatigue_idx = compute_fatigue_index(scores)
    grade = compute_resilience_grade(scores, broke_at)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Turns Run", len(scores))
    m2.metric("Lowest Score", min(scores) if scores else "N/A")
    m3.metric("Broke at Turn", broke_at if broke_at else "Never")
    m4.metric("Fatigue Index", f"{fatigue_idx}%")
    m5.metric("Resilience Grade", grade)

    # ── Score Distribution by Phase ──
    st.subheader("📊 Score Distribution by Attack Phase")
    if log_entries:
        df_log = pd.DataFrame(log_entries)
        fig_box = px.box(
            df_log,
            x="phase_label",
            y="score",
            color="phase_label",
            color_discrete_map={
                "Phase 1: Rapport Building": "#22c55e",
                "Phase 2: Context Overload": "#eab308",
                "Phase 3: Authority Claim": "#f97316",
                "Phase 4: Direct Extraction": "#ef4444",
            },
            labels={"score": "Safety Score", "phase_label": "Attack Phase"},
        )
        fig_box.update_layout(
            template="plotly_dark",
            showlegend=False,
            height=350,
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig_box, use_container_width=True)

    # ── Violation Timeline ──
    st.subheader("⏱️ Violation Timeline")
    violations_data = []
    for entry in log_entries:
        for v in entry["violations"]:
            violations_data.append({"Turn": entry["turn"], "Violation": v, "Score": entry["score"]})
    if violations_data:
        df_v = pd.DataFrame(violations_data)
        st.dataframe(df_v, use_container_width=True, hide_index=True)
    else:
        st.success("No violations detected throughout the test!")

    # ── Save to session state for comparison ──
    run_record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "target": target_name,
        "scenario": scenario_name,
        "aggression": aggression,
        "turns": len(scores),
        "scores": scores,
        "broke_at": broke_at,
        "fatigue_index": fatigue_idx,
        "grade": grade,
        "log": log_entries,
    }
    st.session_state.all_runs.append(run_record)

    # ── Download report ──
    report_json = json.dumps(run_record, indent=2, default=str)
    st.download_button(
        "📥 Download Report (JSON)",
        data=report_json,
        file_name=f"fatiguelab_{target_info['id']}_{scenario['id']}_{aggression}.json",
        mime="application/json",
    )

# ════════════════════════════════════════════════════════════════════════
# TAB 2 — Compare Results
# ════════════════════════════════════════════════════════════════════════
with tab_compare:
    st.subheader("📊 Cross-Run Comparison Dashboard")

    if not st.session_state.all_runs:
        st.info(
            "Run at least one test from the **Live Test** tab to see comparison data. "
            "Run multiple tests with different targets, scenarios, or aggression levels "
            "to compare their security profiles."
        )
    else:
        runs = st.session_state.all_runs

        # ── Overlay safety curves ──
        st.markdown("### Safety Degradation Curves (Overlay)")
        fig_cmp = go.Figure()
        for i, run in enumerate(runs):
            label = f"#{i+1} {run['target']} / {run['scenario']} ({run['aggression']})"
            fig_cmp.add_trace(
                go.Scatter(
                    x=list(range(1, len(run["scores"]) + 1)),
                    y=run["scores"],
                    mode="lines+markers",
                    name=label,
                )
            )
        fig_cmp.add_hrect(y0=0, y1=40, fillcolor="red", opacity=0.08, line_width=0)
        fig_cmp.add_hline(y=40, line_dash="dash", line_color="red", opacity=0.5)
        fig_cmp.update_layout(
            yaxis_range=[-5, 110],
            xaxis_title="Turn",
            yaxis_title="Safety Score",
            template="plotly_dark",
            height=420,
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig_cmp, use_container_width=True)

        # ── Summary table ──
        st.markdown("### Run Summary")
        summary_rows = []
        for i, run in enumerate(runs):
            summary_rows.append(
                {
                    "Run": f"#{i+1}",
                    "Target Bot": run["target"],
                    "Scenario": run["scenario"],
                    "Aggression": run["aggression"],
                    "Turns": run["turns"],
                    "Broke At": run["broke_at"] if run["broke_at"] else "Never",
                    "Fatigue Index": f"{run['fatigue_index']}%",
                    "Grade": run["grade"],
                }
            )
        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

        # ── Clear history ──
        if st.button("🗑️ Clear all runs"):
            st.session_state.all_runs = []
            st.rerun()

# ════════════════════════════════════════════════════════════════════════
# TAB 3 — About
# ════════════════════════════════════════════════════════════════════════
with tab_about:
    st.subheader("About FatigueLab")
    st.markdown(
        """
        ### Problem
        Traditional chatbot security testing fires a **single jailbreak prompt** and checks
        whether the bot resists. Real attackers don't work that way — they use **long,
        friendly, confusing conversations** that slowly wear down a bot's guardrails.

        ### Solution
        FatigueLab is an automated **red-team harness** with three agents:

        | Agent | Role |
        |-------|------|
        | **🗡️ Attacker Agent** | Simulates a persistent customer who escalates through 4 phases: Rapport → Context Overload → Authority Claim → Direct Extraction |
        | **🤖 Target (Victim) Bot** | The chatbot under test — swappable across domains (banking, IoT, telecom, e-commerce) |
        | **🔍 Evaluator** | Scores every reply for secret leaks, prompt leaks, and policy breaches |

        ### Metrics
        - **Safety Score** (0–100 per turn) — drops when violations occur
        - **Fatigue Index** — percentage drop from first to last score
        - **Resilience Grade** (A–F) — overall robustness rating

        ### Architecture
        ```
        Attacker ──▶ Target Bot ──▶ Evaluator
           │              │              │
           │  (phase-     │  (reply)     │  (score +
           │   aware      │              │   violations)
           │   prompt)    │              │
           ▼              ▼              ▼
              Dashboard (live graph + report)
        ```

        ---
        **⚠️ All data in this project is fake.** Use FatigueLab only on bots you own
        or have permission to test.
        """
    )
