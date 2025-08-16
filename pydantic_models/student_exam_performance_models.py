from datetime import date
from typing import List
from pydantic import BaseModel, ConfigDict, Field, field_validator
from constant.constant import ALLOWED_EXAM_TYPE
from pydantic_models.exam_models import ExamStat


# ---------------------------------------------------------------------------
# QUESTION-LEVEL FEEDBACK (persisted)
# ---------------------------------------------------------------------------

class QuestionAnswerFeedbackData(BaseModel):
    """
    Stores marks and qualitative feedback for **one** question in a graded exam.
    """
    model_config = ConfigDict(
        frozen=True,
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "question": "Define Newton's Second Law.",
                "student_answer": "Force equals mass times acceleration.",
                "total_mark": 5,
                "individual_mark": 4,
                "similarity_score": 87,
                "feedback": "Good job! Just missed a bit of detail on the units."
            }
        }
    )

    question: str = Field(..., description="The exam question being evaluated.")
    student_answer: str = Field(..., description="The student's answer to the question.")
    total_mark: int = Field(..., ge=0, description="Maximum marks for this question.")
    individual_mark: int = Field(..., ge=0, description="Marks awarded to the student for this answer.")
    feedback: str = Field(..., description="Qualitative feedback provided for the answer.")


class QuestionAnswerFeedbackDataForInstructor(BaseModel):

    model_config = ConfigDict(
        frozen=True,
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "question": "Define Newton's Second Law.",
                "answer_key": "Force equals mass times acceleration.",
                "student_answer": "Force equals mass times acceleration.",
                "total_mark": 5,
                "individual_mark": 4,
                "similarity_score": 87,
                "feedback": "Good job! Just missed a bit of detail on the units."
            }
        }
    )

    question: str = Field(..., description="The exam question being evaluated.")
    answer_key: str = Field(..., description="The correct answer suggested by instructor for the question")
    student_answer: str = Field(..., description="The student's answer to the question.")
    total_mark: int = Field(..., ge=0, description="Maximum marks for this question.")
    individual_mark: int = Field(..., ge=0, description="Marks awarded to the student for this answer.")
    similarity_score: int = Field(..., description="Similarity score between the student's answer and the recommended one (e.g., from LLM).")
    feedback: str = Field(..., description="Qualitative feedback provided for the answer.")

# ---------------------------------------------------------------------------
# STUDENT-LEVEL FEEDBACK (persisted)
# ---------------------------------------------------------------------------

class StudentExamFeedback(BaseModel):

    model_config = ConfigDict(
        frozen=True,
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "exam_id": "EXAM2025-01",
                "student_id": "stu_4567",
                "question_answer_feedback": [
                    QuestionAnswerFeedbackDataForInstructor.model_config["json_schema_extra"]["example"]
                ],
                "evaluated": True
            }
        }
    )

    exam_id: str = Field(..., description="Unique identifier for the exam.")
    student_id: str = Field(..., description="Unique identifier of the student.")
    question_answer_feedback: List[QuestionAnswerFeedbackDataForInstructor] = Field(
        ..., description="List of question-wise feedback entries."
    )
    evaluated: bool = Field(
        default=False, description="True if evaluation is completed, else False."
    )


# ---------------------------------------------------------------------------
# STUDENT ANSWER SHEET (client-supplied)
# ---------------------------------------------------------------------------

class QuestionAnswerData(BaseModel):
    """
    Raw question + answer pair submitted by the student.
    """
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "question": "Define Newton's Second Law.",
                "answer": "Force equals mass times acceleration."
            }
        }
    )

    question: str = Field(..., description="Question text.")
    answer: str = Field(..., description="Student's response.")


class StudentExamSpecificData(BaseModel):
    """
    Answer sheet for one student sitting a particular exam.
    """
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "student_id": "stu_4567",
                "question_answer": [
                    QuestionAnswerData.model_config["json_schema_extra"]["example"]
                ]
            }
        }
    )

    student_id: str = Field(..., description="ID of the student.")
    question_answer: List[QuestionAnswerData] = Field(
        ..., description="List of question-answer submissions from the student."
    )


# ---------------------------------------------------------------------------
# WRAPPER FOR BULK ADD
# ---------------------------------------------------------------------------

class StudentExamSpecificAddDataRequest(BaseModel):
    """
    API payload: bulk upload of students' answers for one exam.
    """
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "course_name": "Physics",
                "exam_type": "mid_term",
                "data": [
                    StudentExamSpecificData.model_config["json_schema_extra"]["example"]
                ]
            }
        }
    )

    course_name: str = Field(..., description="Name of the course for which the exam was conducted.")
    exam_type: str = Field(..., description="Type of the exam: class_test, mid_term, or final_term.")

    @field_validator("exam_type")
    def check_exam_type(cls, v):
        if v not in ALLOWED_EXAM_TYPE:
            raise ValueError(f"'{v}' is not an allowed exam_type")
        return v

    data: List[StudentExamSpecificData] = Field(
        ..., description="List of student submissions for this exam."
    )


class StudentExamRequest(BaseModel):
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "student_id": "1101",
                "grade": "10",
                "course_name": "Machine Learning",
                "exam_type": "class_test"
            }
        }
    )

    student_id: str = Field(..., description="Unique identifier of the student.")
    grade: str = Field(..., description="Target grade for the exam")
    course_name: str = Field(..., description="Name of the course for which the exam was conducted.")
    exam_type: str = Field(..., description="Type of the exam: class_test, mid_term, or final_term.")

    @field_validator("exam_type")
    def check_exam_type(cls, v):
        if v not in ALLOWED_EXAM_TYPE:
            raise ValueError(f"'{v}' is not an allowed exam_type")
        return v

class StudentPerformanceRequest(BaseModel):
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "student_id": "1101",
                "grade": "10"
            }
        }
    )

    student_id: str = Field(..., description="Unique identifier of the student.")
    grade: str = Field(..., description="Target grade for the exam")


class StudentExamPerformance(BaseModel):
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "course_name": "Machine Learning",
                "exam_type": "1101",
                "exam_stat": ExamStat.model_config["json_schema_extra"]["example"],
                "exam_feedback": [
                    QuestionAnswerData.model_config["json_schema_extra"]["example"]
                ]
            }
        }
    )

    course_name: str = Field(..., description="Name of the course for which the exam was conducted.")
    exam_type: str = Field(..., description="Type of the exam: class_test, mid_term, or final_term.")

    @field_validator("exam_type")
    def check_exam_type(cls, v):
        if v not in ALLOWED_EXAM_TYPE:
            raise ValueError(f"'{v}' is not an allowed exam_type")
        return v

    stats: ExamStat = Field(..., description="Statistics for the exam")
    exam_feedback: List[QuestionAnswerData] = Field(
        ..., description="List of question-answer submissions from the student."
    )

class FixEvaluationFeedback(BaseModel):
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "student_id": "1101",
                "grade": "10",
                "course_name": "Machine Learning",
                "exam_type": "class_test",
                "exam_feedback": [
                    QuestionAnswerFeedbackDataForInstructor.model_config["json_schema_extra"]["example"]
                ]
            }
        }
    )

    student_id: str = Field(..., description="Unique identifier of the student.")
    grade: str = Field(..., description="Target grade for the exam")
    course_name: str = Field(..., description="Name of the course for which the exam was conducted.")
    exam_type: str = Field(..., description="Type of the exam: class_test, mid_term, or final_term.")

    @field_validator("exam_type")
    def check_exam_type(cls, v):
        if v not in ALLOWED_EXAM_TYPE:
            raise ValueError(f"'{v}' is not an allowed exam_type")
        return v

    exam_feedback: List[QuestionAnswerFeedbackDataForInstructor] = Field(
        ..., description="Feedback for student's answers"
    )