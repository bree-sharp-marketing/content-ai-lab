# BT AI Lab — Multi-Stage Content Pipeline (v0.1.0)

A lightweight, prompt-driven, multi-stage AI pipeline for generating structured marketing content.

## What it does

Stages (default order):

1. **stage_1_brief_interpreter** → converts a brief into a JSON blueprint
2. **stage_2_research** → adds structured research notes
3. **stage_3_outline** → creates an outline
4. **stage_4_draft** → writes a draft
5. **stage_5_qa** → checks for alignment + completeness

Outputs a JSON file at `data/output/result.json` by default.

---

## Setup

### 1) Create your env file
Copy the example and add your key:

- `config/.env.example` → `config/.env`

Your `config/.env` should include:

OPENAI_API_KEY=your_key_here

> Note: `config/.env` is intentionally not tracked by git.

### 2) Install dependencies

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
