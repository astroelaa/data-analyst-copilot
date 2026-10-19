import hashlib
from uuid import uuid4

import pandas as pd
import streamlit as st

from src.agent.agent import Session, answer
from src.agent.tools import load_csv
from src.storage import load_chats, save_chat

DEFAULT_CSV = "data/sales.csv"
USER_ERROR = "I couldn't complete that analysis. Please check the question and uploaded data, then try again."
LIMITATION_ERROR = "I couldn't answer that from the available data and analysis tools. Try asking about the columns, values, totals, groups, rankings, or trends in your CSV."


def source_key(source: str, df) -> str:
    columns = ",".join(str(column) for column in df.columns)
    values = pd.util.hash_pandas_object(df, index=True).values.tobytes()
    digest = hashlib.sha256(values).hexdigest()[:16]
    return f"{source}:{len(df)}:{columns}:{digest}"


def restore_history(session: Session, messages: list[dict]) -> None:
    for index, message in enumerate(messages):
        if message.get("type") != "analysis" or index == 0:
            continue
        question = messages[index - 1].get("content", "")
        output = message["output"]
        result = output["result"]
        session.history.append(
            {
                "question": question,
                "ok": result is not None and output.get("error") is None,
                "fixed": output.get("fixed", False),
                "result_columns": list(result.columns) if result is not None else [],
            }
        )

st.set_page_config(page_title="Data Analyst Copilot", layout="wide")
st.title("Data Analyst Copilot")
st.caption("Your general-purpose data analyst for any uploaded CSV. I inspect the data, answer questions, create plans, run pandas analysis, and explain the results.")

with st.sidebar:
    st.subheader("Agent skills")
    st.caption("The agent can use these tools on the uploaded CSV:")
    st.markdown(
        "- **describe_data**: inspect columns, types, and values\n"
        "- **profile_data**: build live schema context for the uploaded CSV\n"
        "- **run_pandas**: execute restricted analysis code\n"
        "- **plot_chart**: create a chart from the result"
    )


upload = st.sidebar.file_uploader("CSV file", type="csv")
source = upload.name if upload else DEFAULT_CSV
df = load_csv(upload or DEFAULT_CSV)
dataset_key = source_key(source, df)
if st.session_state.get("dataset_key") != dataset_key:
    saved = load_chats(dataset_key)
    st.session_state.sessions = {
        chat_id: {**chat, "session": Session(df=df)}
        for chat_id, chat in saved.items()
    }
    if not st.session_state.sessions:
        st.session_state.sessions = {
            f"chat-{uuid4().hex}": {"title": "New chat", "messages": [], "session": Session(df=df)}
        }
    st.session_state.active_session_id = next(iter(st.session_state.sessions))
    st.session_state.source = source
    st.session_state.dataset_key = dataset_key

active_session = st.session_state.sessions[st.session_state.active_session_id]
session = active_session["session"]


def create_chat() -> None:
    chat_id = f"chat-{uuid4().hex}"
    st.session_state.sessions[chat_id] = {
        "title": "New chat",
        "messages": [],
        "session": Session(df=session.df.copy()),
    }
    save_chat(chat_id, st.session_state.dataset_key, "New chat", [])
    st.session_state.active_session_id = chat_id


def render_analysis(output: dict) -> None:
    record = output["record"]
    st.write(output["plan"].goal)
    st.markdown("\n".join(f"{i}. {step}" for i, step in enumerate(output["plan"].steps, start=1)))
    st.code(output["code"], language="python")
    if output["result"] is not None:
        st.dataframe(output["result"], use_container_width=True)
        if output["figure"] is not None:
            st.pyplot(output["figure"])
    else:
        st.error(USER_ERROR)
    tools = [item["tool"] for item in output["trace"]]
    st.caption("Tools used: " + " → ".join(tools))
    with st.expander("What the agent did"):
        st.write("I described and profiled the data, created an analysis plan, ran the pandas code, and prepared the result.")
        st.json(output["trace"])
    with st.expander("Analysis details"):
        st.caption(
            f"tokens {record['input_tokens']}/{record['output_tokens']} | cost {output['cost']:.6f} | auto-fixed {output['fixed']}"
        )
        st.caption("Sources: " + ", ".join(record["citations"]))


st.sidebar.subheader("Chats")
if st.sidebar.button("+ New chat", use_container_width=True):
    create_chat()
    st.rerun()
for chat_id, chat in st.session_state.sessions.items():
    label = chat["title"] or "New chat"
    if st.sidebar.button(label, key=f"select-{chat_id}", use_container_width=True):
        st.session_state.active_session_id = chat_id
        st.rerun()

for chat in st.session_state.sessions.values():
    if not chat["session"].history:
        restore_history(chat["session"], chat["messages"])

for message in active_session["messages"]:
    with st.chat_message(message["role"]):
        if message.get("type") == "analysis":
            render_analysis(message["output"])
        else:
            st.markdown(message["content"])

question = st.chat_input("Ask a question about the data")
if question:
    active_session["messages"].append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        status = st.status("Agent is analyzing your question...", expanded=True)
        status.write("Reading the dataset and checking the available columns.")
        try:
            output = answer(session, question)
        except ValueError:
            status.update(label="Analysis could not be completed", state="error", expanded=False)
            message = LIMITATION_ERROR
            active_session["messages"].append({"role": "assistant", "content": message})
            save_chat(st.session_state.active_session_id, st.session_state.dataset_key, active_session["title"], active_session["messages"])
            st.warning(message)
        except Exception:
            status.update(label="Analysis could not be completed", state="error", expanded=False)
            message = USER_ERROR
            active_session["messages"].append({"role": "assistant", "content": message})
            save_chat(st.session_state.active_session_id, st.session_state.dataset_key, active_session["title"], active_session["messages"])
            st.error(message)
        else:
            record = output["record"]
            status.update(
                label="Analysis complete",
                state="complete",
                expanded=False,
            )
            render_analysis(output)
            active_session["messages"].append({"role": "assistant", "type": "analysis", "output": output})
            if active_session["title"] == "New chat":
                active_session["title"] = question[:32]
            save_chat(st.session_state.active_session_id, st.session_state.dataset_key, active_session["title"], active_session["messages"])

st.sidebar.subheader("Current session history")
for item in session.history:
    status = "ok" if item["ok"] else "failed"
    st.sidebar.write(f"{item['question']} ({status}, fixed={item['fixed']})")
