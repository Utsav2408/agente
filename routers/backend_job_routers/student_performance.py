from fastapi import APIRouter, HTTPException
from pydantic_models.student_exam_performance_models import StudentExamSpecificAddDataRequest
from utils import exam_utils

router = APIRouter(
    tags=["Student Performance"]
)


@router.post("/student/exam/answers")
def add_student_exam_performance(request: StudentExamSpecificAddDataRequest):
    try:
        exam_utils.add_student_answers(
            performance_config=request
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
