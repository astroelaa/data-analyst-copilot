from src.llm.planner import make_plan
from src.rag.store import build_index


def main() -> None:
    build_index()
    while True:
        question = input("question: ").strip()
        if question in ("", "exit"):
            break
        try:
            plan, record = make_plan(question, list(df.columns))
        except ValueError as error:
            print(f"rejected: {error}")
            continue
        print(plan.model_dump_json(indent=2))
        print(record)


if __name__ == "__main__":
    main()
