from fastapi import APIRouter, HTTPException
from mongo_ops.exam_data import update_answer_key
from mongo_ops.student_performance_data import fix_evaluated
from pydantic_models.student_exam_performance_models import FixEvaluationFeedback
from utils import exam_utils
from pydantic_models.exam_models import ExamDataAddRequest, FixAnswerKeyRequest, QuestionAnswerData

router = APIRouter(
    tags=["Exam"]
)


@router.post("/exam")
def add_exam_data(request: ExamDataAddRequest):
    try:
        exam_utils.add_exam(
            exam_config=request.data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))    


@router.post("/exam/answer/keys/fix")
def fix_answer_keys(request: FixAnswerKeyRequest):
    try:
        update_answer_key(request.grade, request.exam_type, request.course_name.replace(" ", "_").lower(), request.question_answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/exam/evaluation/fix")
def evaluation_feedback_fix(request: FixEvaluationFeedback) -> str:
    try:
        fix_evaluated(request.grade, request.exam_type, request.course_name.replace(" ", "_").lower(), request.student_id, request.exam_feedback)
        return "Successfully updated"
    except Exception as e:
        return "Failed update"