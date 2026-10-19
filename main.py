from src.agent.agent import Session, answer
from src.agent.tools import load_csv

DEFAULT_CSV = "data/sales.csv"


def main() -> None:
    session = Session(load_csv(DEFAULT_CSV))
    while True:
        question = input("question: ").strip()
        if question in ("", "exit"):
            break
        try:
            output = answer(session, question)
        except Exception:
            print("I couldn't complete that analysis. Please check the question and uploaded data, then try again.")
            continue
        if output["result"] is None:
            print("I couldn't complete that analysis. Please check the question and uploaded data, then try again.")
            continue
        try:
            print(output["result"].to_string(index=False))
        except Exception:
            print("I couldn't display that result. Please try again.")


if __name__ == "__main__":
    main()
