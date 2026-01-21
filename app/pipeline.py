# app/pipeline.py

from prompts import load_prompt
from app.llm import call_llm
import json
import os


def safe_json(raw: str, stage: str):
    """
    Parse JSON safely and raise a helpful error if the model returns invalid JSON.
    """
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError(f"{stage} returned invalid JSON:\n{raw}")


def stage_1_brief_interpreter(brief: str) -> dict:
    print("🧠 Stage 1: Brief Interpreter (AI)")

    system = load_prompt("brief_interpreter.system")
    raw = call_llm(system, brief)

    blueprint = safe_json(raw, "Stage 1")

    if not isinstance(blueprint, dict):
        raise ValueError(f"Stage 1 expected a JSON object (dict), got: {type(blueprint).__name__}")

    # Optional: enforce required keys so downstream stages don't silently break.
    required = ("objective", "audience", "primary_goal")
    missing = [k for k in required if k not in blueprint]
    if missing:
        raise ValueError(f"Stage 1 JSON missing required keys: {missing}\nReturned:\n{blueprint}")

    return blueprint


def stage_2_research(blueprint: dict) -> dict:
    print("🔍 Stage 2: Research Collector")

    system = load_prompt("research_collector.system")
    raw = call_llm(system, json.dumps(blueprint, ensure_ascii=False))

    research_obj = safe_json(raw, "Stage 2")

    # Stage 2 may return either:
    #  A) {"research": "..."} or {"research": {...}}
    #  B) "..." (string) or {...} (object) if your prompt is looser than intended
    # We normalize to a single "research" value on the pipeline output.
    research_value = None
    if isinstance(research_obj, dict) and "research" in research_obj:
        research_value = research_obj["research"]
    else:
        # If it isn't shaped as {"research": ...}, store the whole parsed object
        # so you don't lose content and you can tighten the prompt later.
        research_value = research_obj

    return {**blueprint, "research": research_value}


def stage_3_outline(data: dict) -> dict:
    print("🧱 Stage 3: Outline Architect")

    system = load_prompt("outline_architect.system")
    raw = call_llm(system, json.dumps(data, ensure_ascii=False))

    outline_obj = safe_json(raw, "Stage 3")
    outline_value = outline_obj["outline"] if isinstance(outline_obj, dict) and "outline" in outline_obj else outline_obj

    return {**data, "outline": outline_value}


def stage_4_draft(data: dict) -> dict:
    print("✍️ Stage 4: Draft Writer")

    system = load_prompt("draft_writer.system")
    raw = call_llm(system, json.dumps(data, ensure_ascii=False))

    draft_obj = safe_json(raw, "Stage 4")
    draft_value = draft_obj["draft"] if isinstance(draft_obj, dict) and "draft" in draft_obj else draft_obj

    return {**data, "draft": draft_value}


def stage_5_qa(data: dict) -> dict:
    print("✅ Stage 5: QA Reviewer")

    system = load_prompt("qa_reviewer.system")
    raw = call_llm(system, json.dumps(data, ensure_ascii=False))

    qa_obj = safe_json(raw, "Stage 5")
    qa_value = qa_obj["qa"] if isinstance(qa_obj, dict) and "qa" in qa_obj else qa_obj

    return {**data, "qa": qa_value}



def write_output(data: dict, output_dir: str = "data/output", filename: str = "result.json") -> str:
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, filename)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return out_path


def run_pipeline(brief: str) -> dict:
    print("\n🚀 Running AI Content Pipeline\n")

    data = stage_1_brief_interpreter(brief)
    data = stage_2_research(data)
    data = stage_3_outline(data)
    data = stage_4_draft(data)
    data = stage_5_qa(data)

    out_path = write_output(data)
    print(f"\n📦 Wrote output: {out_path}")
    print("\n🎉 Pipeline complete\n")

    return data
