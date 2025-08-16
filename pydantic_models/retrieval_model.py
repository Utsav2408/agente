from typing import List
from pydantic import BaseModel, ConfigDict, Field


class SubjectiveQuery(BaseModel):
    """
    Payload used by the API when a user submits a query.
    """
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "query": "What are the differences between mitosis and meiosis?",
                "subject_names": ["Machine Learning", "Data Mining"],
                "grade": "10"
            }
        }
    )

    query: str = Field(
        ...,
        description="Natural language question or prompt submitted by the user.",
    )
    subject_names: List[str] = Field(
        ...,
        description="This contains the list of subject names, query is related to"
    )
    grade: str = Field(
        ...,
        description="The grade of user from whom the query is given"
    )


class SupportQuery(BaseModel):
    """
    Payload used by the API when a user submits a query.
    """
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "query": "What are the differences between mitosis and meiosis?"
            }
        }
    )

    query: str = Field(
        ...,
        description="Natural language question or prompt submitted by the user.",
    )


class RetrievedSubjectiveContext(BaseModel):
    """
    Document returned by the retriever containing contextual information and its source.
    """
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "context": (
                    "Mitosis is the process by which a cell divides to form two identical daughter cells.\n\n"
                    "Meiosis is a special type of cell division that reduces the chromosome number by half."
                ),
                "source": [
                    "Biology Textbook - Chapter 5, Page 12",
                    "Cell Biology Notes - Slide 8"
                ]
            }
        }
    )

    context: str = Field(
        ...,
        description="Combined text of relevant passages, separated by double newlines.",
    )
    source: List[str] = Field(
        ...,
        description="List of source citations, each corresponding to a retrieved context passage",
    )


class RetrievedSupportContext(BaseModel):
    """
    Document returned by the retriever containing contextual information.
    """
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "context": (
                    "Mitosis is the process by which a cell divides to form two identical daughter cells.\n\n"
                    "Meiosis is a special type of cell division that reduces the chromosome number by half."
                )
            }
        }
    )

    context: str = Field(
        ...,
        description="Combined text of relevant passages, separated by double newlines.",
    )

class RetrievedContext(BaseModel):

    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "context": (
                    "Mitosis is the process by which a cell divides to form two identical daughter cells.\n\n"
                    "Meiosis is a special type of cell division that reduces the chromosome number by half."
                )
            }
        }
    )

    context: str = Field(
        ...,
        description="Combined text of relevant passages, separated by double newlines.",
    )
