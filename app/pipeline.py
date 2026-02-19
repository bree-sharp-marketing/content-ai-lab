# app/pipeline.py

import json
import os
import re
from typing import Any, Dict, Set

from prompts import load_prompt
from app.llm import call_llm


def safe_json(raw: str, stage: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError(f"{stage} returned invalid JSON:\n{raw}")


def post_process_draft(draft: str) -> str:
    """Fix known LLM formatting quirks that resist prompt-level correction."""
    # Strip underscore wrappers from CTA link paths:
    # (__/contact__) → (/contact)
    draft = re.sub(r'\(_{1,3}/([^)]+?)_{1,3}\)', r'(/\1)', draft)

    # Replace "Proof" in any H2/H3 heading with safe alternative
    # Catches: "## Proof & ...", "## Proof:", "## Proof and ...", etc.
    def fix_proof_heading(m):
        hashes = m.group(1)
        title = m.group(2)
        # Remove "Proof" and clean up connectors
        cleaned = re.sub(r'\bProof\b\s*[&:]\s*', '', title, flags=re.IGNORECASE)
        cleaned = re.sub(r'\bProof\b', '', cleaned, flags=re.IGNORECASE).strip()
        if not cleaned:
            cleaned = "How We Measure Success"
        return f"{hashes} {cleaned}"
    draft = re.sub(r'^(#{2,3})\s+(.+)$', lambda m: fix_proof_heading(m) if re.search(r'\bproof\b', m.group(2), re.IGNORECASE) else m.group(0), draft, flags=re.MULTILINE)

    # Replace "typically" with "often" everywhere (case-insensitive)
    draft = re.sub(r'\bTypically\b', 'Often', draft)
    draft = re.sub(r'\btypically\b', 'often', draft)

    # Strip "Free " from CTA labels unless brief confirms free consultation
    # [Book Your Free Consultation →] → [Book Your Consultation →]
    draft = re.sub(r'\[([^\]]*?)\bFree\s+', r'[\1', draft)

    return draft


def env_skip(stage_num: int) -> bool:
    """
    Allows skipping stages via env vars:
    SKIP_STAGE_1=1, SKIP_STAGE_2=1, ...
    """
    return os.getenv(f"SKIP_STAGE_{stage_num}", "").strip() in {"1", "true", "True", "YES", "yes"}


def should_run(stage_num: int, fn_name: str, skip_stages: Set[str]) -> bool:
    if fn_name in skip_stages:
        return False
    if env_skip(stage_num):
        return False
    return True


def stage_1_brief_interpreter(brief: str, dry_run: bool = False) -> Dict[str, Any]:
    print("Stage 1: Brief Interpreter (AI)")

    if dry_run:
        return {
            "objective": "placeholder objective",
            "audience": "placeholder audience",
            "primary_goal": "placeholder primary_goal",
        }

    system = load_prompt("brief_interpreter.system")
    raw = call_llm(system, brief)
    blueprint = safe_json(raw, "Stage 1")

    # Optional: assert minimum keys exist
    for key in ("objective", "audience", "primary_goal"):
        if key not in blueprint:
            raise ValueError(f"Stage 1 JSON missing required key: {key}\nReturned:\n{blueprint}")

    return blueprint


def stage_2_research(blueprint: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
    print("Stage 2: Research Collector")

    if dry_run:
        return {**blueprint, "research": "placeholder research"}

    system = load_prompt("research_collector.system")
    raw = call_llm(system, json.dumps(blueprint))
    research_obj = safe_json(raw, "Stage 2")

    # Expecting {"research": "..."} or {"research": {...}}
    if "research" not in research_obj:
        raise ValueError(f"Stage 2 JSON missing 'research' key.\nReturned:\n{research_obj}")

    return {**blueprint, "research": research_obj["research"]}


def stage_3_outline(data: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
    print("Stage 3: Outline Architect")

    if dry_run:
        return {**data, "outline": "placeholder outline"}

    system = load_prompt("outline_architect.system")
    raw = call_llm(system, json.dumps(data))
    outline_obj = safe_json(raw, "Stage 3")

    if "outline" not in outline_obj:
        raise ValueError(f"Stage 3 JSON missing 'outline' key.\nReturned:\n{outline_obj}")

    return {**data, "outline": outline_obj["outline"]}


def stage_4_draft(data: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
    print("Stage 4: Draft Writer")

    if dry_run:
        return {**data, "draft": "placeholder draft"}

    system = load_prompt("draft_writer.system")
    raw = call_llm(system, json.dumps(data))
    draft_obj = safe_json(raw, "Stage 4")

    if "draft" not in draft_obj:
        raise ValueError(f"Stage 4 JSON missing 'draft' key.\nReturned:\n{draft_obj}")

    return {**data, "draft": post_process_draft(draft_obj["draft"])}


def stage_5_voice_harmonizer(data: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
    print("Stage 5: Voice Harmonizer")

    if dry_run:
        return data  # draft stays as-is in dry run

    system = load_prompt("voice_harmonizer.system")
    raw = call_llm(system, json.dumps(data))
    harmonized_obj = safe_json(raw, "Stage 5")

    if "draft" not in harmonized_obj:
        raise ValueError(f"Stage 5 JSON missing 'draft' key.\nReturned:\n{harmonized_obj}")

    return {**data, "draft": post_process_draft(harmonized_obj["draft"])}


def stage_6_qa(data: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
    print("Stage 6: QA Reviewer")

    if dry_run:
        return {**data, "qa": "passed"}

    system = load_prompt("qa_reviewer.system")
    raw = call_llm(system, json.dumps(data))
    qa_obj = safe_json(raw, "Stage 6")

    if "qa" not in qa_obj:
        raise ValueError(f"Stage 6 JSON missing 'qa' key.\nReturned:\n{qa_obj}")

    return {**data, "qa": qa_obj["qa"]}


def write_draft_md(data: Dict[str, Any], output_dir: str) -> str:
    """Save just the draft as a clean, readable Markdown file."""
    draft_path = os.path.join(output_dir, "draft.md")
    draft = data.get("draft", "")
    with open(draft_path, "w", encoding="utf-8") as f:
        f.write(draft)
    print(f"Wrote draft:   {draft_path}")
    return draft_path


def write_summary_md(data: Dict[str, Any], output_dir: str) -> str:
    """Save a full summary with metadata + the draft content."""
    summary_path = os.path.join(output_dir, "summary.md")
    sections = []

    sections.append("# Pipeline Summary\n")

    if data.get("objective"):
        sections.append(f"**Objective:** {data['objective']}\n")
    if data.get("audience"):
        sections.append(f"**Audience:** {data['audience']}\n")
    if data.get("primary_goal"):
        sections.append(f"**Primary Goal:** {data['primary_goal']}\n")

    if data.get("research"):
        sections.append("---\n")
        sections.append("## Research Notes\n")
        sections.append(f"{data['research']}\n")

    if data.get("outline"):
        sections.append("---\n")
        sections.append("## Outline\n")
        sections.append(f"{data['outline']}\n")

    if data.get("draft"):
        sections.append("---\n")
        sections.append("## Draft\n")
        sections.append(f"{data['draft']}\n")

    if data.get("qa"):
        sections.append("---\n")
        sections.append("## QA Review\n")
        sections.append(f"{data['qa']}\n")

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("\n".join(sections))
    print(f"Wrote summary: {summary_path}")
    return summary_path


def write_output(data: Dict[str, Any], output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)

    # Raw JSON (full pipeline data)
    out_path = os.path.join(output_dir, "result.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\nWrote JSON:    {out_path}")

    # Human-readable files
    write_draft_md(data, output_dir)
    write_summary_md(data, output_dir)

    return out_path


def run_pipeline(
    brief: str,
    output_dir: str = "data/output",
    dry_run: bool = False,
    skip_stages: Set[str] | None = None,
) -> Dict[str, Any]:
    """
    skip_stages: set of stage function names to skip (e.g. {"stage_2_research"})
    """
    if skip_stages is None:
        skip_stages = set()

    print("\nRunning AI Content Pipeline\n")

    data: Dict[str, Any] = {}

    if should_run(1, "stage_1_brief_interpreter", skip_stages):
        data = stage_1_brief_interpreter(brief, dry_run=dry_run)
    else:
        print("Skipping Stage 1")

    if should_run(2, "stage_2_research", skip_stages):
        data = stage_2_research(data, dry_run=dry_run)
    else:
        print("Skipping Stage 2")

    if should_run(3, "stage_3_outline", skip_stages):
        data = stage_3_outline(data, dry_run=dry_run)
    else:
        print("Skipping Stage 3")

    if should_run(4, "stage_4_draft", skip_stages):
        data = stage_4_draft(data, dry_run=dry_run)
    else:
        print("Skipping Stage 4")

    if should_run(5, "stage_5_voice_harmonizer", skip_stages):
        data = stage_5_voice_harmonizer(data, dry_run=dry_run)
    else:
        print("Skipping Stage 5")

    if should_run(6, "stage_6_qa", skip_stages):
        data = stage_6_qa(data, dry_run=dry_run)
    else:
        print("Skipping Stage 6")

    write_output(data, output_dir)

    print("\nPipeline complete\n")
    return data
