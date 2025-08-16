from typing import List
from fastapi import APIRouter, HTTPException
from constant.constant import ACADEMIC_YEAR_DEFAULT
from pydantic_models.query_model import Query
from pydantic_models.student_exam_performance_models import QuestionAnswerFeedbackData, StudentExamPerformance, StudentExamRequest, StudentPerformanceRequest
from utils import student_performance_utils
from datetime import datetime
import re
from dateparser.search import search_dates

router = APIRouter(
    tags=["Student Performance"]
)


@router.post(
    path="/student/scorecard",
    operation_id="fetch_exam_scorecard",
    description="Use this function to capture student's scorecard for a given exam"
)
def fetch_exam_scorecard(request: StudentExamRequest) -> List[QuestionAnswerFeedbackData]:
    """
    Use this function to capture student's scorecard for a given exam.

    Args:
        request (StudentExamRequest): The request body containing student's id, grade, course, requested exam_type, and its date.

    Returns:
        A list containing student's performance in each question, along with the original answer given by user.

    Raises:
        HTTPException: If an internal error occurs.
    """
    try:
        return student_performance_utils.fetch_student_exam_record(
            student_data=request
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post(
    path="/student/scorecard/all",
    operation_id="fetch_all_exam_scorecards",
    description="Use this function to capture student's all scorecard records"
)
def fetch_all_exam_scorecards(request: StudentPerformanceRequest) -> List[StudentExamPerformance]:
    """
    Use this function to capture student's all scorecard records.

    Args:
        request (StudentPerformanceRequest): The request body containing student's id and grade.

    Returns:
        A list containing each student's performance in each exam, along with each exam's stat

    Raises:
        HTTPException: If an internal error occurs.
    """
    try:
        return student_performance_utils.fetch_student_all_exam_performance(
            student_data=request
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    path="/resolve/exam/date",
    operation_id="resolve_date_tool",
    description="Use this function to resolve vague or natural language date expressions into a YYYY-MM-DD format date string"
)
def resolve_date_tool(request: Query) -> str:
    """Resolves vague or natural language date expressions into a YYYY-MM-DD format date string.

    If the input does not contain a year, defaults to the academic year.
    Returns the resolved date or an error message.
    """
    settings = {
        "PREFER_DAY_OF_MONTH": "first",
        "PREFER_DATES_FROM": "past",
        "RELATIVE_BASE": datetime(ACADEMIC_YEAR_DEFAULT, 7, 1),
        "RETURN_AS_TIMEZONE_AWARE": False,
        # Helps with “24th August”, “1/9”, etc. (day–month–year bias)
        "DATE_ORDER": "DMY",
    }

    # 1) Find date-like parts inside the full sentence
    hits = search_dates(
        request.query,
        settings=settings,
        languages=["en"],  # keeps it deterministic for English text
    )

    if not hits:
        return (
            "Sorry, I couldn't understand the exam date. "
            "Please provide it in YYYY-MM-DD or a more specific phrase like 'last Monday's midterm'."
        )

    # Take the first detected date ([(matched_substring, datetime_obj), ...])
    _, parsed = hits[0]

    # 2) If the user didn't explicitly include a 4-digit year, force your academic year
    year_explicit = re.search(r"\b\d{4}\b", request.query) is not None
    if not year_explicit:
        parsed = parsed.replace(year=ACADEMIC_YEAR_DEFAULT)
    else:
        # If a year was present but isn't your default, keep user intent UNLESS you want to override:
        if parsed.year != ACADEMIC_YEAR_DEFAULT and str(ACADEMIC_YEAR_DEFAULT) not in request.query:
            # Your previous behavior forced the academic year; keep if desired:
            parsed = parsed.replace(year=ACADEMIC_YEAR_DEFAULT)

    return parsed.strftime("%Y-%m-%d")
