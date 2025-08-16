from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis_db.redis_client import redis_client
from routers.backend_job_routers import course_data, announcement_data, exam_data, grade_data, instructor_data, login_data, student_data, student_performance

@asynccontextmanager
async def lifeSpanOperation(app: FastAPI):
    await redis_client.flush_db()
    yield

app = FastAPI(lifespan=lifeSpanOperation)

# Allow your Streamlit origin (default localhost:8501)
origins = [
    "http://localhost:8501",
    "http://127.0.0.1:8501",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,                 # or ["*"] for dev
    allow_credentials=False,               # True only if you use cookies
    allow_methods=["GET", "OPTIONS"],      # include others if needed
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=[],                     # optional
    max_age=600,                           # optional: cache preflight (seconds)
)

app.include_router(course_data.router)
app.include_router(exam_data.router)
app.include_router(student_performance.router)
app.include_router(student_data.router)
app.include_router(grade_data.router)
app.include_router(instructor_data.router)
app.include_router(login_data.router)
app.include_router(announcement_data.router)

@app.get("/")
async def root():
    return {"message": "Welcome to the Backend Server!"}
