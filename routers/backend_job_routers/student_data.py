from fastapi import APIRouter, HTTPException
from mongo_ops import student_data
from pydantic_models.student_models import StudentDataAddRequest, StudentDataWithoutNumber


router = APIRouter(
    tags=["Student"]
)


@router.get("/student/{student_id}")
def get_student_data(student_id: str) -> StudentDataWithoutNumber:
    try:
        result = student_data.get_student_public(
            student_id=student_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/student")
def add_student_data(request: StudentDataAddRequest) -> None:
    try:
        student_data.add_student(
            student_data=request.data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))