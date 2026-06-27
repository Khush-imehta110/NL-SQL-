from fastapi import FastAPI
from routers.query import router

app = FastAPI()

app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "NL to SQL backend is running!"}