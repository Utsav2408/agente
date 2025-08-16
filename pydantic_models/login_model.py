from datetime import datetime
from enum import Enum
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict

from pydantic_models.exam_models import QuestionAnswerData
from pydantic_models.student_exam_performance_models import QuestionAnswerFeedbackDataForInstructor


# ---------------------------------------------------------------------------
# Role Enumeration
# ---------------------------------------------------------------------------

class UserRole(str, Enum):
    student = "student"
    teacher = "teacher"


# ---------------------------------------------------------------------------
# Incoming User Creation Payload
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "user_id": "john_doe123",
                "password": "securePass123",
                "user_role": "student"
            }
        }
    )

    user_id: str = Field(
        ..., 
        min_length=3, 
        description="Unique user identifier. Must be at least 3 characters long."
    )
    password: str = Field(
        ..., 
        min_length=6, 
        description="Password for the user account. Minimum 6 characters required."
    )
    user_role: UserRole = Field(
        ..., 
        description="Role assigned to the user. Must be either 'student' or 'teacher'."
    )


# ---------------------------------------------------------------------------
# Stored User Data (e.g., in DB or returned in response)
# ---------------------------------------------------------------------------

class UserInDB(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "example": {
                "user_id": "john_doe123",
                "hashed_password": "hashed$2b$12$abc123...",
                "user_role": "student"
            }
        }
    )

    user_id: str = Field(
        ..., 
        description="Unique user identifier as stored in the database."
    )
    hashed_password: str = Field(
        ..., 
        description="Hashed version of the user's password."
    )
    user_role: UserRole = Field(
        ..., 
        description="Role assigned to the user in the system."
    )


# ---------------------------------------------------------------------------
# Login Request
# ---------------------------------------------------------------------------

class UserLogin(BaseModel):
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "user_id": "john_doe123",
                "password": "securePass123"
            }
        }
    )

    user_id: str = Field(
        ..., 
        min_length=3, 
        description="User's unique identifier for login."
    )
    password: str = Field(
        ..., 
        min_length=6, 
        description="Plaintext password provided for authentication."
    )


# ---------------------------------------------------------------------------
# Login Verification Response
# ---------------------------------------------------------------------------

class UserVerifyResponse(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "example": {
                "user_id": "john_doe123",
                "user_role": "student",
                "verified": True,
                "session_token": "eyeyeyeye"
            }
        }
    )

    user_id: str = Field(
        ..., 
        description="Unique identifier of the verified user."
    )
    user_role: UserRole = Field(
        ..., 
        description="Role of the verified user."
    )
    verified: bool = Field(
        True, 
        description="Indicates whether the user’s credentials were successfully verified."
    )
    session_token: str = Field(
        ..., 
        description="JWT token for session auth."
    )

class Turn(BaseModel):
    sender: Literal["user","bot"]
    message: str
    timestamp: datetime

class CustomMemory(BaseModel):
    conversation: List[Turn] = Field(default_factory=list)
    last_route: Optional[str] = None
    last_reason: Optional[str] = None
    last_subject: Optional[List[str]] = None

class Metadata(BaseModel):
    last_support_ticket: str = Field(
        "", description="ID of the last support ticket seen"
    )
    assignee_reply: str = Field(
        "", description="The reply to sent to support ticket on which assignee agreed"
    )
    last_announcement_id: str = Field(
        "", description="ID of the last announcement seen"
    )
    last_announcement_class: str = Field(
        "", description="Class of the last announcement seen"
    )
    last_announcement_summary: str = Field(
        "", description="Summary of the last announcement seen"
    )
    last_announcement_event_date: str = Field(
        "", description="Event date of the last announcement seen"
    )
    last_announcement_title: str = Field(
        "", description="Title of the last announcement seen"
    )
    last_draft_announcement: str = Field(
        "", description="Last draft announcement"
    )
    last_exam: str = Field(
        "", description="Last Exam discussed"
    )
    last_class: str = Field(
        "", description="Last Class discussed"
    )
    last_subject: str = Field(
        "", description="Last Subject discussed"
    )
    last_student_id: str = Field(
        "", description="Last student id"
    )
    last_evaluation_feedback_list: List[QuestionAnswerFeedbackDataForInstructor] = Field(
        [], description="The list of QuestionAnswerFeedbackDataForInstructor"
    )
    last_evaluation_feedback_section: str = Field(
        "", description="Last evaluation feedback response"
    )
    last_question_discussed: int = Field(
        0, description="Last question number discussed"
    )
    last_generated_answer_key: str = Field(
        "", description="Last generated answer keys"
    )
    generated_answer_key_list: List[QuestionAnswerData] = Field(
        [], description="The list of question answer pair for a particular subject's exam"
    )
    last_sub_route: str = Field(
        "", description="Last sub-route the user hit"
    )

class TurnTeacher(BaseModel):
    sender: Literal["user","bot"]
    message: str
    timestamp: datetime
    route: Optional[Literal["ticket_activity", "announcement_activity", "evaluation_activity", "answer_key_generation_activity", "out_of_scope"]] = None
    reason: Optional[Literal["follow_up", "new_query"]] = None
    sub_route: Optional[Literal[
        "support_ticket_detail", "resolve_ticket", "approve_suggestion", "fix_suggestion", 
        "announcement_detail", "announcement_creator", "announcement_approved", "announcement_fix", 
        "evaluation_details", "evaluation_feedback", "approve_feedback", "fix_feedback", 
        "answer_key_details", "approve_answer_key", "fix_answer_key"
    ]] = None

class CustomMemoryTeacher(BaseModel):
    conversation: List[TurnTeacher] = Field(
        [], description="The conversation history of teacher"
    )
    metadata: Metadata = Field(
        default_factory=Metadata,
        description="Tracks the last ticket & sub-route (defaults to empty strings)"
    )

class TokenValidationResponse(BaseModel):
    valid: bool = Field(..., description="Is the token currently valid?")
    user_id: str = Field(None, description="Subject (sub) from the token if valid")
    user_role: str = Field(None, description="Role from the token if valid")
    expires_at: datetime = Field(None, description="Expiration time (UTC) of the token")