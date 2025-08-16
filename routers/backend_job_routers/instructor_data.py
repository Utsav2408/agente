from fastapi import APIRouter, HTTPException
from mongo_ops import instructor_data
from pydantic_models.instructor_models import InstructorDataAddRequest


router = APIRouter(
    tags=["Instructor"]
)


@router.get("/instructor/email/{instructor_email_id}")
def get_instructor_data_by_email_id(instructor_email_id: str):
    try:
        result = instructor_data.get_instructor_data_by_email_id(
            instructor_email_id=instructor_email_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/instructor/{instructor_id}")
def get_instructor_data(instructor_id: str):
    try:
        result = instructor_data.get_instructor_data(
            instructor_id=instructor_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/instructor")
def add_instructor_data(request: InstructorDataAddRequest):
    try:
        instructor_data.add_instructor(
            instructor_data=request.data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
