from typing import List
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# “DATA” MODEL
# ---------------------------------------------------------------------------

class StudentData(BaseModel):
    """
    Object stored in the database that represents a student's full profile.
    """
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "student_id": "stu_001",
                "first_name": "Alice",
                "last_name": "Johnson",
                "contact": ["+1234567890", "+0987654321"],
                "grade": "10",
                "course_ids": ["COURSE101", "COURSE102"]
            }
        }
    )

    student_id: str = Field(..., description="Unique identifier for the student.")
    first_name: str = Field(..., description="First name of the student.")
    last_name: str = Field(..., description="Last name of the student.")
    contact: List[str] = Field(..., description="List of contact numbers associated with the student.")
    grade: str = Field(..., description="Grade or class level of the student.")
    course_ids: List[str] = Field(..., description="List of course IDs the student is enrolled in.")


# ---------------------------------------------------------------------------
# REQUEST MODELS
# ---------------------------------------------------------------------------

class StudentDataAddRequest(BaseModel):
    """
    Payload used by the API when creating a new student.
    """
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "data": StudentData.model_config["json_schema_extra"]["example"]
            }
        }
    )

    data: StudentData = Field(..., description="Object containing full student data.")


class StudentDataWithoutNumber(BaseModel):
    """
    Variant of StudentData that omits phone numbers
    (e.g. for responses where contact info must be hidden).
    """
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "student_id": "stu_001",
                "first_name": "Alice",
                "last_name": "Johnson",
                "grade": "10",
                "course_names": ["Machine Learning", "Data Mining"]
            }
        }
    )

    student_id: str = Field(..., description="Unique identifier for the student.")
    first_name: str = Field(..., description="First name of the student.")
    last_name: str = Field(..., description="Last name of the student.")
    grade: str = Field(..., description="Grade or class level of the student.")
    course_names: List[str] = Field(..., description="List of course names the student is enrolled in.")
