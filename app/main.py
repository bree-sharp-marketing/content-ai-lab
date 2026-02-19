# app/main.py

import argparse
from pathlib import Path

from app.pipeline import run_pipeline


DEFAULT_BRIEF = (
    "Create a service page describing BT Web Group's AI consulting services. "
    "Make it strategy-first, practical, and aimed at generating qualified leads."
)


def read_text_file(path: str) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Brief file not found: {p}")
    return p.read_text(encoding="utf-8").strip()


def parse_args():
    parser = argparse.ArgumentParser(description="Run the BT AI Lab content pipeline.")
    parser.add_argument("--brief", type=str, default=None, help="Brief text to run through the pipeline.")
    parser.add_argument("--brief-file", type=str, default=None, help="Path to a text file containing the brief.")
    parser.add_argument("--out", type=str, default="data/output", help="Output directory (default: data/output).")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without calling the LLM (uses placeholders).",
    )
    parser.add_argument(
        "--skip",
        action="append",
        default=[],
        help="Skip a stage by function name (e.g. --skip stage_2_research). Can be used multiple times.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.brief_file:
        brief = read_text_file(args.brief_file)
    elif args.brief:
        brief = args.brief.strip()
    else:
        brief = DEFAULT_BRIEF

    result = run_pipeline(
        brief=brief,
        output_dir=args.out,
        dry_run=args.dry_run,
        skip_stages=set(args.skip or []),
    )

    print("\nFinal output:")
    print(result)


if __name__ == "__main__":
    main()
