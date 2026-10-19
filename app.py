import streamlit as st

from src.agent.agent import Session, answer
from src.agent.tools import load_csv
from src.rag.store import build_index

DEFAULT_CSV = "data/sales.csv"

st.set_page_config(page_title="Data Analyst Copilot", layout="wide")
st.title("Data Analyst Copilot")
st.caption("Your general-purpose data analyst for any uploaded CSV. I inspect the data, answer questions, create plans, run pandas analysis, and explain the results.")

with st.sidebar:
    st.subheader("Agent skills")
    st.caption("The agent can use these tools on the uploaded CSV:")
    st.markdown(
        "- **describe_data**: inspect columns, types, and values\n"
        "- **run_pandas**: execute restricted analysis code\n"
        "- **plot_chart**: create a chart from the result"
    )


@st.cache_resource
def init_index() -> int:
    return build_index()


try:
    init_index()
except Exception as exc:
    st.warning(f"Semantic search is unavailable: {exc}. Using the local data dictionary instead.")

upload = st.sidebar.file_uploader("CSV file", type="csv")
source = upload.name if upload else DEFAULT_CSV
if st.session_state.get("source") != source:
    df = load_csv(upload or DEFAULT_CSV)
    st.session_state.sessions = {
        "chat-1": {"title": "New chat", "messages": [], "session": Session(df=df)}
    }
    st.session_state.active_session_id = "chat-1"
    st.session_state.source = source
if "sessions" not in st.session_state:
    df = load_csv(upload or DEFAULT_CSV)
    st.session_state.sessions = {
        "chat-1": {"title": "New chat", "messages": [], "session": Session(df=df)}
    }
    st.session_state.active_session_id = "chat-1"

active_session = st.session_state.sessions[st.session_state.active_session_id]
session = active_session["session"]


def create_chat() -> None:
    number = len(st.session_state.sessions) + 1
    chat_id = f"chat-{number}"
    st.session_state.sessions[chat_id] = {
        "title": "New chat",
        "messages": [],
        "session": Session(df=session.df.copy()),
    }
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
        st.error(output["error"])
    tools = [item["tool"] for item in output["trace"]]
    st.caption("Tools used: " + " → ".join(tools))
    with st.expander("What the agent did"):
        st.write("I described the data, created an analysis plan, ran the pandas code, and prepared the result.")
        st.json(output["trace"])
    with st.expander("Analysis details"):
        st.caption(
            f"model {record['model']} | tier {record['tier']} | tokens {record['input_tokens']}/{record['output_tokens']} | cost {output['cost']:.6f} | auto-fixed {output['fixed']}"
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
        except Exception as exc:
            status.update(label="Analysis could not be completed", state="error", expanded=False)
            message = f"I could not complete that analysis: {exc}"
            active_session["messages"].append({"role": "assistant", "content": message})
            st.error(message)
        else:
            record = output["record"]
            status.update(
                label=f"Analysis complete using {record['model']}",
                state="complete",
                expanded=False,
            )
            render_analysis(output)
            active_session["messages"].append({"role": "assistant", "type": "analysis", "output": output})
            if active_session["title"] == "New chat":
                active_session["title"] = question[:32]

st.sidebar.subheader("Current session history")
for item in session.history:
    status = "ok" if item["ok"] else "failed"
    st.sidebar.write(f"{item['question']} ({status}, fixed={item['fixed']})")
