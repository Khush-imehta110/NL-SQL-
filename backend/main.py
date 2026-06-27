from fastapi import FastAPI
from routers.query import router
from services.database import init_db

app = FastAPI()
init_db()

app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "NL to SQL backend is running!"}