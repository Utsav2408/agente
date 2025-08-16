from fastapi import APIRouter, HTTPException
from utils import course_utils
from pydantic_models.course_models import BookAddRequest, CourseAddRequest


router = APIRouter(
    tags=["Course"]
)


@router.post("/course")
def add_course_data(request: CourseAddRequest):
    try:
        course_utils.add_course(
            course_config=request.data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/book")
def add_book_data(request: BookAddRequest):
    try:
        course_utils.add_book(
            course_name=request.course_name,
            book_config=request.data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))