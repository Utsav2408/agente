from typing import List
from pydantic import BaseModel, ConfigDict, Field, field_validator
from constant.constant import ALLOWED_EXAM_TYPE


# ---------------------------------------------------------------------------
# QUESTION MODELS
# ---------------------------------------------------------------------------

class QuestionData(BaseModel):
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "question": "What is the derivative of x^2?",
                "total_mark": 5
            }
        }
    )

    question: str = Field(..., description="This will contain the question")
    total_mark: int = Field(..., ge=0, description="Total marks for the question")


class QuestionAnswerData(BaseModel):
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "question": "What is the derivative of x^2?",
                "total_mark": 5,
                "answer": "2x"
            }
        }
    )

    question: str = Field(..., description="The question")
    total_mark: int = Field(..., ge=0, description="Total marks for the question")
    answer: str = Field(..., description="Correct answer for the question")


# ---------------------------------------------------------------------------
# EXAM DATA – persisted document
# ---------------------------------------------------------------------------

class ExamStat(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "total_marks": 50,
                "highest": 0,
                "lowest": 0,
                "pass_percentage": 0
            }
        }
    )

    total_marks: int = Field(..., ge=0, description="Total marks for the exam")
    highest: int = Field(..., description="Highest mark achieved in an exam")
    lowest: int = Field(..., description="Lowest mark achieved in an exam")
    pass_percentage: int = Field(..., description="Passing percentage of the exam")

class ExamData(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "exam_id": "GRADE:COURSE:EXAM_TYPE",
                "grade": "10",
                "exam_type": "mid_term",
                "course_id": "COURSE101",
                "question_answer": [
                    {
                        "question": "Define Newton's second law.",
                        "total_mark": 5,
                        "answer": "Force equals mass times acceleration (F = ma)"
                    },
                    {
                        "question": "What is 7 + 6?",
                        "total_mark": 2,
                        "answer": "13"
                    }
                ],
                "explored": True,
                "stats": ExamStat.model_config["json_schema_extra"]["example"]
            }
        }
    )

    exam_id: str = Field(..., description="Unique identifier for an exam")
    grade: str = Field(..., description="Target grade for the exam")
    exam_type: str = Field(..., description="Type of the exam: class_test, mid_term, or final_term")

    @field_validator("exam_type")
    def check_exam_type(cls, v):
        if v not in ALLOWED_EXAM_TYPE:
            raise ValueError(f"'{v}' is not an allowed exam_type")
        return v

    course_id: str = Field(..., description="Course ID for which the exam is conducted")
    question_answer: List[QuestionAnswerData] = Field(..., description="Exam questions with answers")
    explored: bool = Field(default=False, description="True if bot finished answering")
    stats: ExamStat = Field(..., description="Statistics for the exam")


# ---------------------------------------------------------------------------
# EXAM SPEC – client-supplied payload
# ---------------------------------------------------------------------------

class ExamDataSpec(BaseModel):
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "grade": "10",
                "exam_type": "mid_term",
                "exam_marks": 50,
                "course_name": "Physics",
                "questions": [
                    {
                        "question": "Define Newton's second law.",
                        "total_mark": 5
                    },
                    {
                        "question": "What is 7 + 6?",
                        "total_mark": 2
                    }
                ]
            }
        }
    )

    grade: str = Field(..., description="Target grade for the exam")
    exam_type: str = Field(..., description="Type of exam: class_test, mid_term, final_term")

    @field_validator("exam_type")
    def check_exam_type_spec(cls, v):
        if v not in ALLOWED_EXAM_TYPE:
            raise ValueError(f"'{v}' is not an allowed exam_type")
        return v

    exam_marks: int = Field(..., ge=0, description="Total marks for the exam")
    course_name: str = Field(..., description="Course name")
    questions: List[QuestionData] = Field(..., description="List of questions")


# ---------------------------------------------------------------------------
# WRAPPER FOR ADD REQUEST
# ---------------------------------------------------------------------------

class ExamDataAddRequest(BaseModel):
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "data": ExamDataSpec.model_config["json_schema_extra"]["example"]
            }
        }
    )

    data: ExamDataSpec = Field(..., description="Exam payload from the client")


class ExamRequest(BaseModel):
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "grade": "10",
                "exam_type": "mid_term",
                "course_name": "Physics"
            }
        }
    )

    grade: str = Field(..., description="The grade/class who gave exam for the particular subject")
    exam_type: str = Field(..., description="Type of exam: class_test, mid_term, final_term")

    @field_validator("exam_type")
    def check_exam_type_spec(cls, v):
        if v not in ALLOWED_EXAM_TYPE:
            raise ValueError(f"'{v}' is not an allowed exam_type")
        return v

    course_name: str = Field(..., description="Course name")


class EvaluationStat(BaseModel):
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "evaluations_completed": 10,
                "evaluations_left": 10,
                "student_ids_left": ["1234", "2344"]
            }
        }
    )

    evaluations_completed: int = Field(..., description="The number of evaluations completed for the exam")
    evaluations_left: int = Field(..., description="The number of evaluations left for the exam")
    student_ids_left: List[str] = Field(..., description="The list of student_ids whose evaluation is left for the exam")


class FixAnswerKeyRequest(BaseModel):
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "grade": "10",
                "exam_type": "mid_term",
                "course_name": "Physics",
                "question_answer": [
                    {
                        "question": "Define Newton's second law.",
                        "total_mark": 5,
                        "answer": "Force equals mass times acceleration (F = ma)"
                    },
                    {
                        "question": "What is 7 + 6?",
                        "total_mark": 2,
                        "answer": "13"
                    }
                ],
            }
        }
    )

    grade: str = Field(..., description="The grade/class who gave exam for the particular subject")
    exam_type: str = Field(..., description="Type of exam: class_test, mid_term, final_term")

    @field_validator("exam_type")
    def check_exam_type_spec(cls, v):
        if v not in ALLOWED_EXAM_TYPE:
            raise ValueError(f"'{v}' is not an allowed exam_type")
        return v

    course_name: str = Field(..., description="Course name")
    question_answer: List[QuestionAnswerData] = Field(..., description="Exam questions with answers")