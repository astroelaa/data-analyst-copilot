import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src import config
from src.schemas import AnalysisPlan


@contextmanager
def _connect():
    path = Path(config.DATABASE_PATH or "data/analyst.db")
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialize_storage() -> None:
    with _connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS chats (
                chat_id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                role TEXT NOT NULL,
                message_type TEXT NOT NULL,
                content TEXT,
                payload TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (chat_id) REFERENCES chats(chat_id)
            );
            """
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _serialize_output(output: dict) -> str:
    result = output["result"]
    payload = {
        "plan": output["plan"].model_dump(mode="json"),
        "code": output["code"],
        "result": result.to_dict(orient="records") if result is not None else None,
        "trace": output["trace"],
        "record": output["record"],
        "cost": output["cost"],
        "fixed": output["fixed"],
        "error": output["error"],
    }
    return json.dumps(payload, default=str)


def _deserialize_output(payload: str) -> dict:
    data = json.loads(payload)
    result = data["result"]
    data["plan"] = AnalysisPlan.model_validate(data["plan"])
    data["result"] = pd.DataFrame(result) if result is not None else None
    data["figure"] = None
    return data


def save_chat(chat_id: str, source: str, title: str, messages: list[dict]) -> None:
    initialize_storage()
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO chats(chat_id, source, title, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET
                source = excluded.source,
                title = excluded.title,
                updated_at = excluded.updated_at
            """,
            (chat_id, source, title, _now()),
        )
        connection.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
        for message in messages:
            is_analysis = message.get("type") == "analysis"
            connection.execute(
                """
                INSERT INTO messages(chat_id, role, message_type, content, payload, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    chat_id,
                    message["role"],
                    "analysis" if is_analysis else "text",
                    None if is_analysis else message.get("content"),
                    _serialize_output(message["output"]) if is_analysis else None,
                    _now(),
                ),
            )


def load_chats(source: str) -> dict[str, dict]:
    initialize_storage()
    with _connect() as connection:
        chats = connection.execute(
            "SELECT chat_id, title FROM chats WHERE source = ? ORDER BY updated_at",
            (source,),
        ).fetchall()
        loaded = {}
        for chat in chats:
            rows = connection.execute(
                """
                SELECT role, message_type, content, payload
                FROM messages WHERE chat_id = ? ORDER BY id
                """,
                (chat["chat_id"],),
            ).fetchall()
            messages = []
            for row in rows:
                if row["message_type"] == "analysis":
                    messages.append(
                        {
                            "role": row["role"],
                            "type": "analysis",
                            "output": _deserialize_output(row["payload"]),
                        }
                    )
                else:
                    messages.append({"role": row["role"], "content": row["content"]})
            loaded[chat["chat_id"]] = {"title": chat["title"], "messages": messages}
        return loaded
