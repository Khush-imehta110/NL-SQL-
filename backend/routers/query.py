from fastapi import APIRouter, UploadFile, File, Form
from services.duck import query_csv
from services.llm import generate_sql
from services.database import save_query
import duckdb
import shutil
import os
import json

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/query")
async def query(file: UploadFile = File(...), question: str = Form(...)):
    try:
        filepath = os.path.join(UPLOAD_DIR, file.filename)
        filepath = filepath.replace("\\", "/")

        with open(filepath, "wb") as f:
            shutil.copyfileobj(file.file, f)

        columns = duckdb.execute(
            f"DESCRIBE SELECT * FROM read_csv_auto('{filepath}')"
        ).fetchdf()["column_name"].tolist()

        sql = generate_sql(question, columns)
        sql = sql.replace("```sql", "").replace("```", "").strip()

        result = query_csv(filepath, sql)
        result_dict = result.to_dict(orient="records")

        save_query(
            filename=file.filename,
            question=question,
            sql_query=sql,
            result=json.dumps(result_dict)
        )

        return {
            "question": question,
            "sql": sql,
            "result": result_dict
        }
    except Exception as e:
        return {"error": str(e)}
    
@router.get("/history")
def get_query_history():
    from services.database import get_history
    rows = get_history()
    history = []
    for row in rows:
        history.append({
            "id": row[0],
            "filename": row[1],
            "question": row[2],
            "sql_query": row[3],
            "result": json.loads(row[4]),
            "created_at": row[5]
        })
    return history