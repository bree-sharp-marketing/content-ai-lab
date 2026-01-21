from pathlib import Path

PROMPTS_DIR = Path(__file__).parent  # the /prompts folder

def load_prompt(name: str) -> str:
    """
    Loads a prompt file from the prompts directory.

    Example:
      load_prompt("brief_interpreter.system") -> reads prompts/brief_interpreter.system
    """
    path = PROMPTS_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return path.read_text(encoding="utf-8")
