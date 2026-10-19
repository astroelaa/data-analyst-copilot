from pathlib import Path

from src.llm.planner import make_plan

DICTIONARY = Path("data/data_dictionary.md").read_text(encoding="utf-8")


def main() -> None:
    while True:
        question = input("question: ").strip()
        if question in ("", "exit"):
            break
        plan, record = make_plan(question, DICTIONARY)
        print(plan.model_dump_json(indent=2))
        print(record)


if __name__ == "__main__":
    main()
