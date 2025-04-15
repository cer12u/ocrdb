from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg

from app.api import router

app = FastAPI()

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(router, prefix="/api")

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
