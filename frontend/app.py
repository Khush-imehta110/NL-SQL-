import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="NL to SQL", page_icon="🔍", layout="wide")
st.title("🔍 Ask Your Data")
st.markdown("Upload any CSV and ask questions in plain English.")

tab1, tab2 = st.tabs(["🔍 Query", "🕐 History"])

with tab1:
    uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

    if uploaded_file:
        df_preview = pd.read_csv(uploaded_file)
        st.subheader("📄 Data Preview")
        st.dataframe(df_preview.head(5))

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Rows", df_preview.shape[0])
        with col2:
            st.metric("Columns", df_preview.shape[1])

        uploaded_file.seek(0)

        st.subheader("💬 Ask a Question")
        question = st.text_input("Type your question in plain English",
                                  placeholder="e.g. Which passenger class had the highest survival rate?")

        if st.button("Ask"):
            if question:
                with st.spinner("Thinking..."):
                    response = requests.post(
                        f"{API_URL}/query",
                        files={"file": (uploaded_file.name, uploaded_file, "text/csv")},
                        data={"question": question}
                    )
                    data = response.json()

                if "error" in data:
                    st.error(f"Error: {data['error']}")
                else:
                    st.subheader("🧠 Generated SQL")
                    st.code(data["sql"], language="sql")

                    st.subheader("📊 Results")
                    result_df = pd.DataFrame(data["result"])
                    st.dataframe(result_df)

                    numeric_cols = result_df.select_dtypes(include="number").columns.tolist()
                    text_cols = result_df.select_dtypes(exclude="number").columns.tolist()

                    if len(numeric_cols) > 0 and len(result_df) > 1:
                        st.subheader("📈 Chart")
                        if text_cols:
                            st.bar_chart(result_df.set_index(text_cols[0])[numeric_cols[0]])
                        else:
                            st.bar_chart(result_df[numeric_cols[0]])
            else:
                st.warning("Please type a question first!")

with tab2:
    st.subheader("🕐 Query History")
    if st.button("Refresh History"):
        st.rerun()

    response = requests.get(f"{API_URL}/history")
    history = response.json()

    if not history:
        st.info("No queries yet. Ask something in the Query tab!")
    else:
        for item in history:
            with st.expander(f"📁 {item['filename']} — {item['question']} ({item['created_at']})"):
                st.code(item["sql_query"], language="sql")
                st.dataframe(pd.DataFrame(item["result"]))

st.markdown("---")
st.markdown("Built with FastAPI + DuckDB + Groq AI + SQLite")