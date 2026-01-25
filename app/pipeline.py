# app/pipeline.py

import json
import os
from typing import Any, Dict, Set

from prompts import load_prompt
from app.llm import call_llm


def safe_json(raw: str, stage: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError(f"{stage} returned invalid JSON:\n{raw}")


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
    print("🧠 Stage 1: Brief Interpreter (AI)")

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
    print("🔍 Stage 2: Research Collector")

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
    print("🧱 Stage 3: Outline Architect")

    if dry_run:
        return {**data, "outline": "placeholder outline"}

    # If you want Stage 3 prompt-driven later, you can add:
    # system = load_prompt("outline_architect.system")
    # raw = call_llm(system, json.dumps(data))
    # outline_obj = safe_json(raw, "Stage 3")
    # return {**data, "outline": outline_obj["outline"]}

    return {**data, "outline": "placeholder outline"}


def stage_4_draft(data: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
    print("✍️ Stage 4: Draft Writer")

    if dry_run:
        return {**data, "draft": "placeholder draft"}

    return {**data, "draft": "placeholder draft"}


def stage_5_qa(data: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
    print("✅ Stage 5: QA Reviewer")

    if dry_run:
        return {**data, "qa": "passed"}

    return {**data, "qa": "passed"}


def write_output(data: Dict[str, Any], output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "result.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\n📦 Wrote output: {out_path}")
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

    print("\n🚀 Running AI Content Pipeline\n")

    data: Dict[str, Any] = {}

    if should_run(1, "stage_1_brief_interpreter", skip_stages):
        data = stage_1_brief_interpreter(brief, dry_run=dry_run)
    else:
        print("⏭️  Skipping Stage 1")

    if should_run(2, "stage_2_research", skip_stages):
        data = stage_2_research(data, dry_run=dry_run)
    else:
        print("⏭️  Skipping Stage 2")

    if should_run(3, "stage_3_outline", skip_stages):
        data = stage_3_outline(data, dry_run=dry_run)
    else:
        print("⏭️  Skipping Stage 3")

    if should_run(4, "stage_4_draft", skip_stages):
        data = stage_4_draft(data, dry_run=dry_run)
    else:
        print("⏭️  Skipping Stage 4")

    if should_run(5, "stage_5_qa", skip_stages):
        data = stage_5_qa(data, dry_run=dry_run)
    else:
        print("⏭️  Skipping Stage 5")

    write_output(data, output_dir)

    print("\n🎉 Pipeline complete\n")
    return data
