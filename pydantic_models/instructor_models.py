from typing import List
from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# “DATA” MODEL
# ---------------------------------------------------------------------------

class InstructorData(BaseModel):
    """
    Object stored in the database that represents a single instructor.
    """
    model_config = ConfigDict(
        frozen=True,
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "instructor_id": "1001",
                "instructor_name": "Dr. Jane Doe",
                "instructor_email_id": "jane.doe@example.com",
                "course_names": ["Machine Learning", "Data Mining"]
            }
        }
    )

    instructor_id: str = Field(
        ...,
        description="Unique identifier for the instructor",
    )
    instructor_name: str = Field(
        ...,
        description="Full name of the instructor",
    )
    instructor_email_id: str = Field(
        ...,
        description="Email ID of the instructor",
    )
    course_names: List[str] = Field(
        ..., 
        description="List of courses the instructor is assigned"
    )


# ---------------------------------------------------------------------------
# REQUEST MODEL
# ---------------------------------------------------------------------------

class InstructorDataAddRequest(BaseModel):
    """
    Payload used by the API when creating a new instructor.
    """
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "data": InstructorData.model_config["json_schema_extra"]["example"]
            }
        }
    )

    data: InstructorData = Field(
        ...,
        description="Payload containing instructor information",
    )
