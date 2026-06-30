from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_sql(question: str, columns: list[str]) -> str:
    prompt = f"""
    You are a SQL expert. Given a table called 'data' with these columns: {columns}
    Write a single DuckDB SQL query to answer this question: {question}
    Return ONLY the SQL query, nothing else, no explanation, no markdown.
    """
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def explain_result(question: str, sql: str, result: list[dict]) -> dict:
    prompt = f"""
    A user asked: "{question}"
    SQL query ran: {sql}
    Result returned: {result}

    Do two things:
    1. Explain what this result means in 2-3 simple sentences. Be specific about the numbers.
    2. Suggest exactly 3 follow-up questions the user might want to ask next about this data.

    Respond in this exact JSON format with no markdown:
    {{
        "explanation": "your explanation here",
        "followup_questions": ["question 1", "question 2", "question 3"]
    }}
    """
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    import json
    text = response.choices[0].message.content.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except Exception:
        return {
            "explanation": text,
            "followup_questions": []
        }
    
def generate_dataset_summary(columns: list, stats: dict, missing: dict, outliers: list) -> str:
    prompt = f"""
    You are a senior data scientist. Analyze this dataset and give exactly 5 bullet point insights.
    
    Columns: {columns}
    Statistics: {stats}
    Missing values: {missing}
    Outliers: {outliers}
    
    Give 5 specific, numbered insights a data analyst would find valuable.
    Be specific with numbers. No markdown, no headers, just 5 numbered points.
    """
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()