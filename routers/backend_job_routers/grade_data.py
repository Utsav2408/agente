from fastapi import APIRouter, HTTPException
from mongo_ops import grade_data
from pydantic_models.grade_models import GradeDataAddRequest


router = APIRouter(
    tags=["FAQ"]
)


@router.get("/grade/{grade}")
def get_grade_data(grade: str):
    try:
        result = grade_data.get_grade_data(
            grade=grade
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/grade")
def add_grade_data(request: GradeDataAddRequest):
    try:
        grade_data.add_grade(
            grade_data=request.data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
