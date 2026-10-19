import streamlit as st

from src.agent.agent import Session, answer
from src.agent.tools import load_csv
from src.rag.store import build_index

DEFAULT_CSV = "data/sales.csv"

st.set_page_config(page_title="Data Analyst Copilot", layout="wide")
st.title("Data Analyst Copilot")
st.caption("Your English-language data analyst for sales.csv. I create plans, run pandas analysis, and explain the results.")


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
    st.session_state.session = Session(df=load_csv(upload or DEFAULT_CSV))
    st.session_state.source = source
session = st.session_state.session
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Ask a question about the data")
if question:
    st.session_state.messages.append({"role": "user", "content": question})
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
            st.session_state.messages.append({"role": "assistant", "content": message})
            st.error(message)
        else:
            record = output["record"]
            status.update(
                label=f"Analysis complete using {record['model']}",
                state="complete",
                expanded=False,
            )
            st.write(output["plan"].goal)
            st.markdown("\n".join(f"{i}. {step}" for i, step in enumerate(output["plan"].steps, start=1)))
            st.code(output["code"], language="python")
            if output["result"] is not None:
                st.dataframe(output["result"])
                if output["figure"] is not None:
                    st.pyplot(output["figure"])
            else:
                st.error(output["error"])
            with st.expander("What the agent did"):
                st.write("I described the data, created an analysis plan, ran the pandas code, and prepared the result.")
                st.json(output["trace"])
            with st.expander("Analysis details"):
                st.caption(
                    f"model {record['model']} | tier {record['tier']} | tokens {record['input_tokens']}/{record['output_tokens']} | cost {output['cost']:.6f} | auto-fixed {output['fixed']}"
                )
                st.caption("Sources: " + ", ".join(record["citations"]))
            st.session_state.messages.append(
                {"role": "assistant", "content": output["plan"].goal}
            )

st.sidebar.subheader("Session history")
for item in session.history:
    status = "ok" if item["ok"] else "failed"
    st.sidebar.write(f"{item['question']} ({status}, fixed={item['fixed']})")
