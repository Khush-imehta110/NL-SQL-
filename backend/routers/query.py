from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from services.duck import query_csv
from services.llm import generate_sql, explain_result
from services.database import save_query
import duckdb
import shutil
import os
import json

router = APIRouter()

UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".csv"}
os.makedirs(UPLOAD_DIR, exist_ok=True)

def validate_file(file: UploadFile):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")

def validate_sql(sql: str):
    sql_upper = sql.upper().strip()
    dangerous = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "EXEC", "TRUNCATE"]
    for keyword in dangerous:
        if keyword in sql_upper:
            raise HTTPException(status_code=400, detail=f"Unsafe SQL detected: {keyword}")

@router.post("/query")
async def query(request: Request, file: UploadFile = File(...), question: str = Form(...)):
    validate_file(file)
    filepath = None
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

        validate_sql(sql)

        result = query_csv(filepath, sql)
        result_dict = result.to_dict(orient="records")

        save_query(
            filename=file.filename,
            question=question,
            sql_query=sql,
            result=json.dumps(result_dict)
        )

        explanation = explain_result(question, sql, result_dict[:5])

        return {
            "question": question,
            "sql": sql,
            "result": result_dict,
            "explanation": explanation.get("explanation", ""),
            "followup_questions": explanation.get("followup_questions", [])
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)

@router.post("/schema")
async def get_schema(file: UploadFile = File(...)):
    validate_file(file)
    filepath = None
    try:
        filepath = os.path.join(UPLOAD_DIR, file.filename)
        filepath = filepath.replace("\\", "/")

        with open(filepath, "wb") as f:
            shutil.copyfileobj(file.file, f)

        schema = duckdb.execute(
            f"DESCRIBE SELECT * FROM read_csv_auto('{filepath}')"
        ).fetchdf()

        return schema.to_dict(orient="records")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)

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

@router.delete("/history")
def clear_history():
    from services.database import clear_all_history
    clear_all_history()
    return {"message": "History cleared"}