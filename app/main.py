# app/main.py

from app.pipeline import run_pipeline


def main():
    brief = "AI consulting service page for BT Web Group"
    result = run_pipeline(brief)

    print("📦 Final output:")
    print(result)


if __name__ == "__main__":
    main()
