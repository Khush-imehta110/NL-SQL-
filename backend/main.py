from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from routers.query import router
from services.database import init_db

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="NL to SQL API",
    description="Ask questions about your CSV data in plain English",
    version="1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()
app.include_router(router)

@app.get("/")
@limiter.limit("20/hour")
def read_root(request: Request):
    return {"message": "NL to SQL API is running!"}