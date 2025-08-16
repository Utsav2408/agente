from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from routers.mcp_routers import exam_data, student_performance, support_ticket_data, announcement_data, retriever_data

app = FastAPI()

app.include_router(exam_data.router)
app.include_router(student_performance.router)
app.include_router(support_ticket_data.router)
app.include_router(announcement_data.router)

app.include_router(retriever_data.router)

mcp = FastApiMCP(app)
mcp.mount()

@app.get("/")
async def root():
    return {"message": "Welcome to the Backend Server!"}
