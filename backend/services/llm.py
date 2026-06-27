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