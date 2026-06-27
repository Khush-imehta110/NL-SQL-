from fastapi import APIRouter, UploadFile, File, Form
from services.duck import query_csv
from services.llm import generate_sql
import duckdb
import shutil
import os

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

        return {
            "question": question,
            "sql": sql,
            "result": result.to_dict(orient="records")
        }
    except Exception as e:
        return {"error": str(e)}