from typing import List
from pydantic import BaseModel, ConfigDict, Field


class InstructorQueryRequest(BaseModel):
    """
    Payload used by the API when an instructor raises a query.
    """
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "query": "How can I update the exam schedule for grade 9?",
                "instructor_id": "inst_1234",
                "instructor_email": "john@gmail.com",
                "available_subjects": ['Machine Learning', 'Data Mining']
            }
        }
    )

    query: str = Field(
        ...,
        description="The content of the query raised by the instructor.",
    )
    instructor_id: str = Field(
        ...,
        description="Unique identifier of the instructor raising the query."
    )
    instructor_email: str = Field(
        ...,
        description="Email ID of the instructor",
    )
    available_subjects: List[str] = Field(
        ...,
        description="The list of subjects, the instructor is assigned"
    )

class StudentQueryRequest(BaseModel):
    """
    Payload used by the API when a user raises a query.
    """
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "query": "How can I update the exam schedule for grade 9?",
                "id": "inst_1234",
                "available_subjects": ['Machine Learning', 'Data Mining'],
                "grade": "10"
            }
        }
    )

    query: str = Field(
        ...,
        description="The content of the query raised by the instructor.",
    )
    id: str = Field(
        ...,
        description="Unique identifier of the user raising the query."
    )
    available_subjects: List[str] = Field(
        ...,
        description="The list of subjects, the user has access to"
    )
    grade: str = Field(
        ...,
        description="Grade of the user posting the query"
    )

class Query(BaseModel):
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "query": "How can I update the exam schedule for grade 9?"
            }
        }
    )

    query: str = Field(
        ...,
        description="The content of the query raised by the instructor.",
    ) 

class QueryList(BaseModel):
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "query_list": ["How to submit my assignment?", "What is Canvas"]
            }
        }
    )

    query_list: List[str] = Field(
        ...,
        description="The list of queries generated based on user query",
    )


class AnswerList(BaseModel):
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "answer_list": ["This is how it works.", "I hope it is done"]
            }
        }
    )

    answer_list: List[str] = Field(
        ...,
        description="The list of answers generated for each query passed",
    )