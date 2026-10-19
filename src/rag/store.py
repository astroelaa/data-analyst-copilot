import re
from pathlib import Path

import chromadb

from src.rag.embeddings import embed

DICTIONARY_PATH = Path("data/data_dictionary.md")
DB_PATH = "chroma_db"
COLLECTION = "data_dictionary"
ENTRY = re.compile(r"^- (\w+) \(")


def load_entries(path: Path = DICTIONARY_PATH) -> list[dict]:
    entries = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        match = ENTRY.match(line)
        if match:
            entries.append(
                {"column": match.group(1), "text": line[2:], "line": number, "source": path.as_posix()}
            )
    return entries


def known_columns() -> set[str]:
    return {entry["column"] for entry in load_entries()}


def build_index() -> int:
    entries = load_entries()
    collection = chromadb.PersistentClient(path=DB_PATH).get_or_create_collection(
        COLLECTION, metadata={"hnsw:space": "cosine"}
    )
    collection.upsert(
        ids=[entry["column"] for entry in entries],
        documents=[entry["text"] for entry in entries],
        embeddings=embed([entry["text"] for entry in entries], "RETRIEVAL_DOCUMENT"),
        metadatas=[
            {"column": entry["column"], "line": entry["line"], "source": entry["source"]}
            for entry in entries
        ],
    )
    return len(entries)


def retrieve(question: str, k: int = 5) -> list[dict]:
    collection = chromadb.PersistentClient(path=DB_PATH).get_collection(COLLECTION)
    result = collection.query(
        query_embeddings=embed([question], "RETRIEVAL_QUERY"), n_results=k
    )
    return [
        {
            "column": meta["column"],
            "text": document,
            "line": meta["line"],
            "source": meta["source"],
            "distance": round(distance, 4),
        }
        for document, meta, distance in zip(
            result["documents"][0], result["metadatas"][0], result["distances"][0]
        )
    ]


def citation(chunk: dict) -> str:
    return f"{chunk['source']}:L{chunk['line']} ({chunk['column']})"
