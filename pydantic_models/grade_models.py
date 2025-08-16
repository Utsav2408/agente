from typing import List
from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# “DATA” MODEL
# ---------------------------------------------------------------------------

class InstructorCourseMapping(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "course_name": "Mathematics",
                "instructor_email_id": "math_teacher@example.com"
            }
        }
    )

    course_name: str = Field(
        ...,
        description="Name of the course assigned to the instructor",
    )
    instructor_email_id: str = Field(
        ...,
        description="Email ID of the instructor for the given course",
    )


class GradeData(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "grade": "10",
                "mapping": [
                    {
                        "course_name": "Mathematics",
                        "instructor_email_id": "math_teacher@example.com"
                    },
                    {
                        "course_name": "Science",
                        "instructor_email_id": "science_teacher@example.com"
                    }
                ],
                "grade_head_email_id": "grade10_head@example.com"
            }
        }
    )

    grade: str = Field(
        ...,
        description="Unique identifier of the grade",
    )
    mapping: List[InstructorCourseMapping] = Field(
        ...,
        description="List mapping each course to its instructor's email ID",
    )
    grade_head_email_id: str = Field(
        ...,
        description="Email ID of the head instructor for the grade",
    )


# ---------------------------------------------------------------------------
# REQUEST MODEL
# ---------------------------------------------------------------------------

class GradeDataAddRequest(BaseModel):
    """
    Payload used by the API when creating a new grade entry.
    """
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "data": GradeData.model_config["json_schema_extra"]["example"]
            }
        }
    )

    data: GradeData = Field(
        ...,
        description="Grade object containing instructor-course mappings",
    )
