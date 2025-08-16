from fastapi import FastAPI
from routers.crew_routers import student_crew_route, teacher_crew_route

app = FastAPI(
    title="Crew Server",
    version="1.0"
)

app.include_router(student_crew_route.router)
app.include_router(teacher_crew_route.router)

@app.get("/")
async def root():
    return {"message": "Welcome to the Crew Server!"}
