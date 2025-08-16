from typing import List
from fastapi import APIRouter, HTTPException
from mongo_ops.exam_data import fetch_question_answer, submit_answer_key
from mongo_ops.student_performance_data import evaluation_data, fetch_evaluation_feedback, mark_evaluated
from pydantic_models.student_exam_performance_models import QuestionAnswerFeedbackDataForInstructor, StudentExamRequest
from pydantic_models.exam_models import EvaluationStat, ExamRequest, QuestionAnswerData

router = APIRouter(
    tags=["Exam"]
)


@router.post(
    path="/exam/evaluation",
    operation_id="evaluation_details",
    description="Use this function to fetch the details on how far the evaluation of student's answers within a class for a particular subject's exam is completed"
)
def evaluation_details(request: ExamRequest) -> EvaluationStat:
    """
    Use this function to fetch the details on how far the evaluation of student's answers within a class for a particular subject's exam is completed.

    Args:
        request (ExamRequest): The request body containing grade/class, exam_type, course_name

    Returns:
        An object consisting of evaluations_completed, evaluations_left, and list of student_ids whose evaluation is still left.

    Raises:
        HTTPException: If an internal error occurs.
    """
    try:
        return evaluation_data(request.grade, request.exam_type, request.course_name.replace(" ", "_").lower())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post(
    path="/exam/evaluation/suggested",
    operation_id="get_evaluation_feedback",
    description="Use this function to provide suggested evaluation feedback"
)
def get_evaluation_feedback(request: StudentExamRequest) -> List[QuestionAnswerFeedbackDataForInstructor]:
    """
    Use this function to provide suggested evaluation feedback

    Args:
        request (StudentExamRequest): The request body containing student's id, grade, course and requested exam_type

    Returns:
        A list containing suggested evaluation for each question in the exam.

    Raises:
        HTTPException: If an internal error occurs.
    """
    try:
        return fetch_evaluation_feedback(request.grade, request.exam_type, request.course_name.replace(" ", "_").lower(), request.student_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post(
    path="/exam/evaluation/submit",
    operation_id="evaluation_feedback_submit",
    description="Use this function to mark the student's answers for a particular exam"
)
def evaluation_feedback_submit(request: StudentExamRequest) -> str:
    """
    Use this function to mark the student's answers for a particular exam

    Args:
        request (StudentExamRequest): The request body containing student's id, grade, course and requested exam_type

    Returns:
        A str indicating the success or failure to update the database for marking student's answers.

    Raises:
        HTTPException: If an internal error occurs.
    """
    try:
        mark_evaluated(request.grade, request.exam_type, request.course_name.replace(" ", "_").lower(), request.student_id)
        return "Successfully marked student's answers"
    except Exception as e:
        return "Failed marked student's answers"


@router.post(
    path="/exam/answer/keys",
    operation_id="fetch_answer_keys",
    description="Use this function to fetch answer keys for a particular exam"
)
def fetch_answer_keys(request: ExamRequest) -> List[QuestionAnswerData]:
    """
    Use this function to fetch answer keys for a particular exam

    Args:
        request (ExamRequest): The request body containing grade/class, exam_type, course_name

    Returns:
        A list of objects having question, answer key and total_marks

    Raises:
        HTTPException: If an internal error occurs.
    """
    try:
        return fetch_question_answer(request.grade, request.exam_type, request.course_name.replace(" ", "_").lower())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    path="/exam/answer/keys/submit",
    operation_id="answer_key_submit",
    description="Use this function to approve the answer keys for a particular exam"
)
def answer_key_submit(request: ExamRequest) -> str:
    """
    Use this function to approve the answer keys for a particular exam

    Args:
        request (ExamRequest): The request body containing grade/class, exam_type, course_name

    Returns:
        A str with success or failure message

    Raises:
        HTTPException: If an internal error occurs.
    """
    try:
        submit_answer_key(request.grade, request.exam_type, request.course_name.replace(" ", "_").lower())
        return "Successfully updated the answer keys"
    except Exception as e:
        print(e)
        return "Failed updating answer keys"