import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="NL to SQL", page_icon="🔍", layout="wide")
st.title("🔍 Ask Your Data")
st.markdown("Upload any CSV and ask questions in plain English.")

with st.sidebar:
    st.header("💡 Sample Questions")
    st.markdown("Try these on the Titanic dataset:")
    sample_questions = [
        "How many passengers survived?",
        "Which class had highest survival rate?",
        "Average age of passengers by class?",
        "How many male vs female passengers?",
        "Top 5 passengers who paid highest fare?",
        "What is the survival rate by gender?",
        "Average fare by passenger class?"
    ]
    for q in sample_questions:
        st.markdown(f"- {q}")
    st.markdown("---")
    st.markdown("**How it works:**")
    st.markdown("1. Upload any CSV file")
    st.markdown("2. Type a question")
    st.markdown("3. AI generates SQL")
    st.markdown("4. See results instantly")
    st.markdown("---")
    st.markdown("**Chart types:**")
    st.markdown("📊 Bar — comparisons")
    st.markdown("📈 Line — trends")
    st.markdown("🔵 Scatter — correlations")
    st.markdown("🥧 Pie — proportions")

tab1, tab2, tab3 = st.tabs(["🔍 Query", "📊 Data Analysis", "🕐 History"])

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
            try:
                schema_response = requests.post(
                    f"{API_URL}/schema",
                    files={"file": (uploaded_file.name, uploaded_file, "text/csv")}
                )
                schema_df = pd.DataFrame(schema_response.json())
                st.dataframe(schema_df)
            except Exception:
                st.error("Could not connect to backend. Make sure FastAPI is running.")

        uploaded_file.seek(0)

        st.subheader("💬 Ask a Question")
        prefill = st.session_state.pop("prefill_question", "")
        question = st.text_input(
            "Type your question in plain English",
            value=prefill,
            placeholder="e.g. Which passenger class had the highest survival rate?"
        )

        col_ask, col_chart = st.columns([3, 1])
        with col_chart:
            chart_type = st.selectbox(
                "Chart type",
                ["Auto", "Bar", "Line", "Scatter", "Pie", "None"]
            )

        if st.button("Ask", type="primary"):
            if question:
                with st.spinner("Thinking..."):
                    try:
                        uploaded_file.seek(0)
                        response = requests.post(
                            f"{API_URL}/query",
                            files={"file": (uploaded_file.name, uploaded_file, "text/csv")},
                            data={"question": question}
                        )
                        data = response.json()
                    except Exception:
                        st.error("Cannot connect to backend. Make sure FastAPI is running on port 8000.")
                        st.stop()

                if "error" in data:
                    st.error(f"Something went wrong: {data['error']}")
                    st.info("💡 Try rephrasing your question. Example: 'How many passengers per class?' instead of 'passenger class count'")
                else:
                    st.success("Query executed successfully!")

                    st.subheader("🧠 Generated SQL")
                    st.code(data["sql"], language="sql")

                    st.subheader("📊 Results")
                    result_df = pd.DataFrame(data["result"])

                    if result_df.empty:
                        st.warning("No results found. Try a different question.")
                    else:
                        st.dataframe(result_df)
                        if data.get("explanation"):
                          st.subheader("🤖 AI Insight")
                        st.info(data["explanation"])

                    if data.get("followup_questions"):
                        st.subheader("💡 Suggested Follow-up Questions")
                        for q in data["followup_questions"]:
                            if st.button(q, key=f"followup_{q}"):
                                st.session_state["prefill_question"] = q
                                st.rerun()

                        csv_download = result_df.to_csv(index=False).encode("utf-8")
                        st.download_button(
                            label="⬇️ Download Results as CSV",
                            data=csv_download,
                            file_name="results.csv",
                            mime="text/csv"
                        )

                        numeric_cols = result_df.select_dtypes(include="number").columns.tolist()
                        text_cols = result_df.select_dtypes(exclude="number").columns.tolist()

                        if len(result_df) == 1 and len(numeric_cols) > 0:
                            st.subheader("📌 Result")
                            metric_cols = st.columns(len(numeric_cols))
                            for i, col in enumerate(numeric_cols):
                                with metric_cols[i]:
                                    val = result_df[col].iloc[0]
                                    st.metric(col, round(val, 2) if isinstance(val, float) else val)

                        elif len(result_df) > 1 and len(numeric_cols) > 0 and chart_type != "None":
                            st.subheader("📈 Chart")

                            try:
                                chart_df = result_df.copy()
                                chart_df.columns = [
                                    col.replace("(", "_").replace(")", "_").replace(" ", "_")
                                    for col in chart_df.columns
                                ]
                                numeric_clean = chart_df.select_dtypes(include="number").columns.tolist()
                                text_clean = chart_df.select_dtypes(exclude="number").columns.tolist()

                                effective_type = chart_type
                                if chart_type == "Auto":
                                    if len(result_df) <= 10:
                                        effective_type = "Bar"
                                    else:
                                        effective_type = "Line"

                                if effective_type == "Bar":
                                    if text_clean:
                                        st.bar_chart(chart_df.set_index(text_clean[0])[numeric_clean[0]])
                                    else:
                                        st.bar_chart(chart_df[numeric_clean[0]])

                                elif effective_type == "Line":
                                    if text_clean:
                                        st.line_chart(chart_df.set_index(text_clean[0])[numeric_clean[0]])
                                    else:
                                        st.line_chart(chart_df[numeric_clean[0]])

                                elif effective_type == "Scatter":
                                    if len(numeric_clean) >= 2:
                                        st.scatter_chart(chart_df[numeric_clean[:2]])
                                    else:
                                        st.info("Scatter chart needs at least 2 numeric columns.")

                                elif effective_type == "Pie":
                                    import plotly.express as px
                                    if text_clean:
                                        fig = px.pie(
                                            chart_df,
                                            names=text_clean[0],
                                            values=numeric_clean[0]
                                        )
                                        st.plotly_chart(fig)
                                    else:
                                        st.info("Pie chart needs a text column for labels.")

                            except Exception as e:
                                st.info(f"Chart could not be generated for this result type. The data is still shown in the table above.")

                        elif chart_type != "None" and len(numeric_cols) == 0:
                            st.info("💡 No numeric data in results — chart not applicable here.")
            else:
                st.warning("Please type a question first!")
    else:
        st.info("👆 Upload a CSV file to get started.")

with tab2:
    st.subheader("📊 Full Data Analysis")
    uploaded_file2 = st.file_uploader("Upload CSV for analysis", type=["csv"], key="analysis")

    if uploaded_file2:
        df_analysis = pd.read_csv(uploaded_file2)

        with st.spinner("Running full analysis..."):
            uploaded_file2.seek(0)
            eda_response = requests.post(
                f"{API_URL}/eda",
                files={"file": (uploaded_file2.name, uploaded_file2, "text/csv")}
            )
            eda = eda_response.json()

        quality = eda["quality_score"]
        score = quality["score"]

        st.subheader("🏆 Data Quality Score")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Overall Score", f"{score}/100")
        with col2:
            st.metric("Grade", quality["grade"])
        with col3:
            st.metric("Missing Score", f"{quality['missing_score']}/40")
        with col4:
            st.metric("Duplicate Score", f"{quality['duplicate_score']}/30")

        if score >= 80:
            st.success(f"✅ Data quality is Excellent ({score}/100)")
        elif score >= 60:
            st.warning(f"⚠️ Data quality is Good but can be improved ({score}/100)")
        else:
            st.error(f"❌ Data needs cleaning before analysis ({score}/100)")

        st.markdown("---")

        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("📋 Summary Statistics")
            st.dataframe(df_analysis.describe())

            st.subheader("🔍 Missing Values")
            missing = df_analysis.isnull().sum()
            missing = missing[missing > 0]
            if missing.empty:
                st.success("No missing values found!")
            else:
                missing_df = pd.DataFrame({
                    "Column": missing.index,
                    "Missing Count": missing.values,
                    "Missing %": (missing.values / len(df_analysis) * 100).round(2)
                })
                st.dataframe(missing_df)

            st.subheader("👥 Duplicate Rows")
            dupes = eda["duplicates"]
            st.metric("Duplicate Rows", f"{dupes['duplicate_rows']} ({dupes['duplicate_percentage']}%)")

        with col_right:
            st.subheader("🎯 Unique Value Counts")
            unique_df = pd.DataFrame(eda["unique_counts"])
            st.dataframe(unique_df)

            st.subheader("⚠️ Outliers (IQR Method)")
            outlier_df = pd.DataFrame(eda["outliers"])
            if not outlier_df.empty:
                st.dataframe(outlier_df)
            else:
                st.success("No numeric columns for outlier detection.")

        st.markdown("---")

        st.subheader("🔥 Correlation Heatmap")
        corr_data = eda.get("correlation", {})
        if corr_data:
            import plotly.figure_factory as ff
            import plotly.graph_objects as go
            corr_values = corr_data["values"]
            corr_cols = corr_data["columns"]
            fig = go.Figure(data=go.Heatmap(
                z=corr_values,
                x=corr_cols,
                y=corr_cols,
                colorscale="RdBu",
                zmid=0,
                text=[[str(round(v, 2)) for v in row] for row in corr_values],
                texttemplate="%{text}",
                showscale=True
            ))
            fig.update_layout(title="Correlation Matrix", height=500)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Need at least 2 numeric columns for correlation heatmap.")

        st.markdown("---")
        st.subheader("🤖 AI Dataset Insights")
        if eda.get("ai_summary"):
            st.info(eda["ai_summary"])

        st.markdown("---")
        st.subheader("📊 Column Distributions")
        numeric_cols = df_analysis.select_dtypes(include="number").columns.tolist()
        text_cols = df_analysis.select_dtypes(exclude="number").columns.tolist()

        if numeric_cols:
            col_dist, col_type = st.columns([3, 1])
            with col_dist:
                selected_col = st.selectbox("Select numeric column", numeric_cols)
            with col_type:
                dist_type = st.selectbox("Chart type", ["Histogram", "Box Plot"])

            import plotly.express as px
            if dist_type == "Histogram":
                fig = px.histogram(df_analysis, x=selected_col,
                                 title=f"Distribution of {selected_col}",
                                 color_discrete_sequence=["#636EFA"])
                fig.update_layout(bargap=0.1)
                st.plotly_chart(fig, use_container_width=True)
            else:
                fig = px.box(df_analysis, y=selected_col,
                           title=f"Box Plot — {selected_col}",
                           color_discrete_sequence=["#636EFA"])
                st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("🔵 Scatter Plot")
        if len(numeric_cols) >= 2:
            col1, col2, col3 = st.columns(3)
            with col1:
                x_col = st.selectbox("X axis", numeric_cols, index=0)
            with col2:
                y_col = st.selectbox("Y axis", numeric_cols, index=1)
            with col3:
                color_col = st.selectbox("Color by", ["None"] + text_cols)
            
            if color_col == "None":
                fig = px.scatter(df_analysis, x=x_col, y=y_col,
                               title=f"{x_col} vs {y_col}")
            else:
                fig = px.scatter(df_analysis, x=x_col, y=y_col,
                               color=color_col,
                               title=f"{x_col} vs {y_col} by {color_col}")
            st.plotly_chart(fig, use_container_width=True)

        if text_cols:
            st.markdown("---")
            st.subheader("📝 Categorical Distributions")
            selected_cat = st.selectbox("Select categorical column", text_cols)
            value_counts = df_analysis[selected_cat].value_counts().head(15).reset_index()
            value_counts.columns = [selected_cat, "count"]
            fig = px.bar(value_counts, x=selected_cat, y="count",
                        title=f"Value Counts — {selected_cat}",
                        color_discrete_sequence=["#636EFA"])
            st.plotly_chart(fig, use_container_width=True)


with tab3:
    st.subheader("🕐 Query History")
    col_refresh, col_clear = st.columns([1, 1])
    with col_refresh:
        if st.button("🔄 Refresh"):
            st.rerun()
    with col_clear:
        if st.button("🗑️ Clear History"):
            try:
                requests.delete(f"{API_URL}/history")
                st.success("History cleared!")
                st.rerun()
            except Exception:
                st.error("Could not clear history.")

    try:
        response = requests.get(f"{API_URL}/history")
        history = response.json()

        if not history:
            st.info("No queries yet. Ask something in the Query tab!")
        else:
            st.markdown(f"**{len(history)} queries saved**")
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
    except Exception:
        st.error("Cannot connect to backend.")

st.markdown("---")
st.markdown("Built with FastAPI + DuckDB + Groq AI + SQLite")