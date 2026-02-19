import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv("config/.env")

# Safety check
if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY not found in config/.env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("MODEL_NAME", "gpt-4.1")


def call_llm(system_prompt: str, user_prompt: str) -> str:
    response = client.responses.create(
        model=MODEL,
        instructions=system_prompt,
        input=user_prompt,
        max_output_tokens=16000,
    )
    return response.output_text
