from typing import List
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# “DATA” MODEL – persisted announcement
# ---------------------------------------------------------------------------

class Announcement(BaseModel):
    """
    Record that is stored in the database once an announcement is scheduled
    (and later marked as posted).
    """
    model_config = ConfigDict(
        frozen=True,
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "announcement_id": "1234",
                "grade": "10",
                "title": "Math Olympiad",
                "poster_email": "utsavvora0809@gmail.com",
                "content": "Math Olympiad on Friday. Prepare well!",
                "posting_date": "2025-07-08",
                "event_date": "2025-07-11"
            }
        }
    )

    announcement_id: str = Field(
        ..., 
        description="Unique Identifier for the announcement"
    )
    grade: str = Field(
        ...,
        description="The grade for which the announcement is intended",
    )
    title: str = Field(
        ...,
        description="The title of the announcement",
    )
    poster_email: str = Field(
        ...,
        description="Email of the person making the announcement",
    )
    content: str = Field(
        ...,
        description="The main content of the announcement",
    )
    posting_date: str = Field(
        ...,
        description="The date when the announcement should be posted",
    )
    event_date: str = Field(
        ...,
        description="The date of the event mentioned in the announcement",
    )


# ---------------------------------------------------------------------------
# SPEC MODEL – client request to create an announcement
# ---------------------------------------------------------------------------

class AnnouncementSpec(BaseModel):
    """
    Payload supplied by the client when scheduling a new announcement.
    """
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "grade": "10",
                "poster_email": "utsavvora0809@gmail.com",
                "title": "Math Olympiad",
                "content": "Math Olympiad on Friday. Prepare well!",
                "event_date": "2025-07-11"
            }
        }
    )

    grade: str = Field(
        ...,
        description="The grade level the announcement is intended for",
    )
    poster_email: str = Field(
        ...,
        description="Email of the person making the announcement",
    )
    title: str = Field(
        ...,
        description="The title of the announcement",
    )
    content: str = Field(
        ...,
        description="The main content of the announcement",
    )
    event_date: str = Field(
        ...,
        description="The date of the event mentioned in the announcement",
    )


# ---------------------------------------------------------------------------
# WRAPPER FOR ADD REQUEST
# ---------------------------------------------------------------------------

class AnnouncementAddRequest(BaseModel):
    """
    API wrapper used when a client submits an announcement to be scheduled.
    """
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "data": {
                    "grade": "10",
                    "poster_email": "utsavvora0809@gmail.com",
                    "title": "Math Olympiad",
                    "content": "Math Olympiad on Friday. Prepare well!",
                    "event_date": "2025-07-11"
                }
            }
        }
    )

    data: AnnouncementSpec = Field(
        ...,
        description="The data for the new announcement to be scheduled",
    )

class AnnouncementID(BaseModel):
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "announcement_id": "1234"
            }
        }
    )

    announcement_id: str = Field(..., description="Unique Identifier for an announcement")

class AnnouncementDetails(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "announcement_id": "1234",
                "grade": "10",
                "title": "Math Olympiad",
                "content": "Math Olympiad on Friday. Prepare well!",
                "posting_date": "2025-07-08",
                "event_date": "2025-07-11"
            }
        }
    )

    announcement_id: str = Field(
        ..., 
        description="Unique Identifier for the announcement"
    )
    grade: str = Field(
        ...,
        description="The grade level the announcement is intended for",
    )
    title: str = Field(
        ...,
        description="The title of the announcement",
    )
    content: str = Field(
        ...,
        description="The main content of the announcement",
    )
    posting_date: str = Field(
        ...,
        description="The date when the announcement should be posted",
    )
    event_date: str = Field(
        ...,
        description="The date of the event mentioned in the announcement",
    )

class AnnouncementData(BaseModel):
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "data": [AnnouncementDetails.model_config["json_schema_extra"]["example"]]
            }
        }
    )

    data: List[AnnouncementDetails] = Field(
        ...,
        description="Announcements created by the user"
    )