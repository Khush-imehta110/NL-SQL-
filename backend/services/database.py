import sqlite3
import os
from datetime import datetime

DB_PATH = "history.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS query_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            question TEXT,
            sql_query TEXT,
            result TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_query(filename: str, question: str, sql_query: str, result: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO query_history (filename, question, sql_query, result, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (filename, question, sql_query, result, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_history():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM query_history ORDER BY created_at DESC LIMIT 20')
    rows = cursor.fetchall()
    conn.close()
    return rows