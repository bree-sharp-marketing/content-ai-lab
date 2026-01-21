# app/pipeline.py

import json
from prompts import load_prompt

from app.llm import call_llm


def stage_1_brief_interpreter(brief: str):
    print("🧠 Stage 1: Brief Interpreter (AI)")

    system = load_prompt("brief_interpreter.system")

    raw = call_llm(system, brief)

    try:
        blueprint = json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError(f"Stage 1 returned invalid JSON:\n{raw}")

    return blueprint




def stage_2_research(blueprint: dict):
    system = load_prompt("research_collector.system")
    raw = call_llm(system, json.dumps(blueprint))
    research = json.loads(raw)
    return {**blueprint, "research": research}

def safe_json(raw, stage):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError(f"{stage} returned invalid JSON:\n{raw}")


def stage_3_outline(data: dict):
    print("🧱 Stage 3: Outline Architect")
    return {**data, "outline": "placeholder outline"}


def stage_4_draft(data: dict):
    print("✍️ Stage 4: Draft Writer")
    return {**data, "draft": "placeholder draft"}


def stage_5_qa(data: dict):
    print("✅ Stage 5: QA Reviewer")
    return {**data, "qa": "passed"}


def run_pipeline(brief: str):
    print("\n🚀 Running AI Content Pipeline\n")

    data = stage_1_brief_interpreter(brief)
    data = stage_2_research(data)
    data = stage_3_outline(data)
    data = stage_4_draft(data)
    data = stage_5_qa(data)

    print("\n🎉 Pipeline complete\n")
    return data
