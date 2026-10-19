from src.llm.router import ask


def main() -> None:
    while True:
        question = input("question: ").strip()
        if question in ("", "exit"):
            break
        answer, record = ask(question)
        print(answer)
        print(record)


if __name__ == "__main__":
    main()
