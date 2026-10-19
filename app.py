import streamlit as st

from src.agent.agent import Session, answer
from src.agent.tools import load_csv
from src.rag.store import build_index

DEFAULT_CSV = "data/sales.csv"

st.set_page_config(page_title="Data Analyst Copilot", layout="wide")
st.title("Data Analyst Copilot")
st.caption("Ask questions in English. The data dictionary in data/data_dictionary.md describes sales.csv.")


@st.cache_resource
def init_index() -> int:
    return build_index()


init_index()

upload = st.sidebar.file_uploader("CSV file", type="csv")
source = upload.name if upload else DEFAULT_CSV
if st.session_state.get("source") != source:
    st.session_state.session = Session(df=load_csv(upload or DEFAULT_CSV))
    st.session_state.source = source
session = st.session_state.session

question = st.chat_input("Ask a question about the data")
if question:
    try:
        output = answer(session, question)
    except ValueError as exc:
        st.error(str(exc))
    else:
        st.subheader("Plan")
        st.write(output["plan"].goal)
        st.markdown("\n".join(f"{i}. {step}" for i, step in enumerate(output["plan"].steps, start=1)))
        st.subheader("Code")
        st.code(output["code"], language="python")
        if output["result"] is not None:
            st.subheader("Result")
            st.dataframe(output["result"])
            if output["figure"] is not None:
                st.pyplot(output["figure"])
        else:
            st.error(output["error"])
        with st.expander("Tool trace"):
            st.json(output["trace"])
        record = output["record"]
        st.caption(
            f"model {record['model']} | tier {record['tier']} | tokens {record['input_tokens']}/{record['output_tokens']} | cost {output['cost']:.6f} | auto-fixed {output['fixed']}"
        )
        st.caption("Sources: " + ", ".join(record["citations"]))

st.sidebar.subheader("Session history")
for item in session.history:
    status = "ok" if item["ok"] else "failed"
    st.sidebar.write(f"{item['question']} ({status}, fixed={item['fixed']})")
