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

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Rows", df_preview.shape[0])
        with col2:
            st.metric("Columns", df_preview.shape[1])
        with col3:
            st.metric("Size", f"{uploaded_file.size // 1024} KB")

        tab_preview, tab_schema = st.tabs(["📄 Data Preview", "🗂️ Schema"])

        with tab_preview:
            st.dataframe(df_preview.head(10))

        with tab_schema:
            uploaded_file.seek(0)
            schema_response = requests.post(
                f"{API_URL}/schema",
                files={"file": (uploaded_file.name, uploaded_file, "text/csv")}
            )
            schema_df = pd.DataFrame(schema_response.json())
            st.dataframe(schema_df)

        uploaded_file.seek(0)

        st.subheader("💬 Ask a Question")
        question = st.text_input(
            "Type your question in plain English",
            placeholder="e.g. Which passenger class had the highest survival rate?"
        )

        if st.button("Ask", type="primary"):
            if question:
                with st.spinner("Thinking..."):
                    response = requests.post(
                        f"{API_URL}/query",
                        files={"file": (uploaded_file.name, uploaded_file, "text/csv")},
                        data={"question": question}
                    )
                    data = response.json()

                if "error" in data:
                    st.error(f"Something went wrong: {data['error']}")
                    st.info("Try rephrasing your question.")
                else:
                    st.success("Query executed successfully!")

                    st.subheader("🧠 Generated SQL")
                    st.code(data["sql"], language="sql")

                    st.subheader("📊 Results")
                    result_df = pd.DataFrame(data["result"])
                    st.dataframe(result_df)

                    csv_download = result_df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="⬇️ Download Results as CSV",
                        data=csv_download,
                        file_name="results.csv",
                        mime="text/csv"
                    )

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
                result_df = pd.DataFrame(item["result"])
                st.dataframe(result_df)
                csv_download = result_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="⬇️ Download",
                    data=csv_download,
                    file_name="history_result.csv",
                    mime="text/csv",
                    key=f"download_{item['id']}"
                )

st.markdown("---")
st.markdown("Built with FastAPI + DuckDB + Groq AI + SQLite")