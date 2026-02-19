"""
BT AI Lab — Streamlit UI
Run with:  streamlit run streamlit_app.py
"""

import json
import os
import sys
import time
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Make sure project modules are importable
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.pipeline import (
    stage_1_brief_interpreter,
    stage_2_research,
    stage_3_outline,
    stage_4_draft,
    stage_5_voice_harmonizer,
    stage_6_qa,
    write_output,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="BT AI Lab",
    page_icon="🧪",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Sidebar — brief selection + pipeline controls
# ---------------------------------------------------------------------------
st.sidebar.title("BT AI Lab")
st.sidebar.markdown("---")

# Discover available brief files
BRIEFS_DIR = PROJECT_ROOT / "data" / "briefs"
brief_files = sorted(BRIEFS_DIR.glob("*.txt")) if BRIEFS_DIR.exists() else []
brief_names = {f.stem.replace("-", " ").title(): f for f in brief_files}

brief_source = st.sidebar.radio(
    "Brief source",
    ["Select a saved brief", "Paste custom brief"],
    index=0,
)

brief_text = ""

if brief_source == "Select a saved brief":
    if brief_names:
        chosen = st.sidebar.selectbox("Choose brief", list(brief_names.keys()))
        brief_text = brief_names[chosen].read_text(encoding="utf-8")
    else:
        st.sidebar.warning("No `.txt` files found in `data/briefs/`.")
else:
    brief_text = st.sidebar.text_area(
        "Paste your brief here",
        height=200,
        placeholder="Write a service page for...",
    )

st.sidebar.markdown("---")

# Stage skip toggles
st.sidebar.markdown("**Skip stages**")
skip_1 = st.sidebar.checkbox("Brief Interpreter", value=False)
skip_2 = st.sidebar.checkbox("Research Collector", value=False)
skip_3 = st.sidebar.checkbox("Outline Architect", value=False)
skip_4 = st.sidebar.checkbox("Draft Writer", value=False)
skip_5 = st.sidebar.checkbox("Voice Harmonizer", value=False)
skip_6 = st.sidebar.checkbox("QA Reviewer", value=False)

dry_run = st.sidebar.checkbox("Dry run (no LLM calls)", value=False)

run_button = st.sidebar.button("Run Pipeline", type="primary", use_container_width=True)

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
st.title("BT AI Lab")
st.caption("Content pipeline powered by AI agents")

# Show the brief
with st.expander("Brief preview", expanded=False):
    st.text(brief_text[:2000] if brief_text else "(no brief loaded)")

# ---------------------------------------------------------------------------
# Pipeline execution
# ---------------------------------------------------------------------------
STAGES = [
    (1, "stage_1_brief_interpreter", "Brief Interpreter", skip_1),
    (2, "stage_2_research", "Research Collector", skip_2),
    (3, "stage_3_outline", "Outline Architect", skip_3),
    (4, "stage_4_draft", "Draft Writer", skip_4),
    (5, "stage_5_voice_harmonizer", "Voice Harmonizer", skip_5),
    (6, "stage_6_qa", "QA Reviewer", skip_6),
]

STAGE_FNS = {
    1: lambda data, dr: stage_1_brief_interpreter(data, dry_run=dr),
    2: lambda data, dr: stage_2_research(data, dry_run=dr),
    3: lambda data, dr: stage_3_outline(data, dry_run=dr),
    4: lambda data, dr: stage_4_draft(data, dry_run=dr),
    5: lambda data, dr: stage_5_voice_harmonizer(data, dry_run=dr),
    6: lambda data, dr: stage_6_qa(data, dry_run=dr),
}

if run_button:
    if not brief_text.strip():
        st.error("Please provide a brief before running the pipeline.")
        st.stop()

    # Progress bar + status
    progress = st.progress(0, text="Starting pipeline...")
    status_box = st.empty()

    data = {}
    total = len(STAGES)
    t0 = time.time()

    for idx, (num, fn_name, label, skip) in enumerate(STAGES):
        pct = int((idx / total) * 100)
        progress.progress(pct, text=f"Stage {num}: {label}...")

        if skip:
            status_box.info(f"Skipping Stage {num}: {label}")
            time.sleep(0.3)
            continue

        status_box.info(f"Running Stage {num}: {label}...")

        try:
            if num == 1:
                data = STAGE_FNS[num](brief_text, dry_run)
            else:
                data = STAGE_FNS[num](data, dry_run)
        except Exception as e:
            progress.progress(pct, text=f"Stage {num} failed")
            st.error(f"Stage {num} ({label}) failed:\n\n```\n{e}\n```")
            st.stop()

    elapsed = time.time() - t0
    progress.progress(100, text="Pipeline complete!")
    status_box.success(f"Done in {elapsed:.1f}s")

    # Save outputs
    output_dir = str(PROJECT_ROOT / "data" / "output")
    write_output(data, output_dir)

    # Store in session state so tabs persist
    st.session_state["pipeline_data"] = data
    st.session_state["run_time"] = elapsed

# ---------------------------------------------------------------------------
# Results display (persists via session_state)
# ---------------------------------------------------------------------------
if "pipeline_data" in st.session_state:
    data = st.session_state["pipeline_data"]

    st.markdown("---")

    tab_draft, tab_qa, tab_outline, tab_research, tab_blueprint, tab_json = st.tabs(
        ["Draft", "QA Review", "Outline", "Research", "Blueprint", "Raw JSON"]
    )

    with tab_draft:
        draft = data.get("draft", "")
        if draft:
            st.markdown(draft, unsafe_allow_html=False)
        else:
            st.info("No draft generated.")

    with tab_qa:
        qa = data.get("qa", "")
        if qa:
            if "PASS WITH NOTES" in str(qa).upper():
                st.warning(qa)
            elif "PASS" in str(qa).upper():
                st.success(qa)
            elif "FAIL" in str(qa).upper():
                st.error(qa)
            else:
                st.info(qa)
        else:
            st.info("No QA review.")

    with tab_outline:
        outline = data.get("outline", "")
        if outline:
            st.markdown(f"```\n{outline}\n```")
        else:
            st.info("No outline generated.")

    with tab_research:
        research = data.get("research", "")
        if research:
            st.markdown(f"```\n{research}\n```")
        else:
            st.info("No research generated.")

    with tab_blueprint:
        meta_keys = ["objective", "audience", "primary_goal", "content_type",
                     "tone", "draft_mode", "proof_level", "page_type", "notes", "questions"]
        for k in meta_keys:
            val = data.get(k)
            if val:
                st.markdown(f"**{k.replace('_', ' ').title()}:** {val}")

    with tab_json:
        st.json(data)
