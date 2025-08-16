from typing import List
from bson import ObjectId
from pymongo.collection import Collection

from config.mongo_connect import mongo
from constant.constant import PERFORMANCE_COLLECTION, PERFORMANCE_DB
from mongo_ops.utils import _to_doc
from pydantic_models.exam_models import EvaluationStat
from pydantic_models.student_exam_performance_models import QuestionAnswerFeedbackData, QuestionAnswerFeedbackDataForInstructor, StudentExamFeedback


_student_col: Collection = mongo.get_connection()[PERFORMANCE_DB][PERFORMANCE_COLLECTION]

def add_student_specific_exam_info(student_exam_feedback: StudentExamFeedback) -> ObjectId:
    """
    Insert a new student performance in exam record.

    Returns
    -------
    bson.ObjectId
        The MongoDB `_id` of the newly inserted document.
    """
    result = _student_col.insert_one(_to_doc(student_exam_feedback))
    return result.inserted_id


def fetch_student_specific_exam_info(exam_id: str, student_id: str) -> List[QuestionAnswerFeedbackData]:
    """
    Retrieve a student specific exam info document by exam_id and student_id identifiers.

    Returns
    -------
    List of QuestionAnswerFeedbackData
    """
    doc = _student_col.find_one(
        {"student_id": student_id, "exam_id": exam_id},
        {"_id": 0},  # hide internal Mongo ID
    )
    return [
        QuestionAnswerFeedbackData.model_validate(question_answer_feedback)
        for question_answer_feedback in doc.get("question_answer_feedback", [])
    ]


def fetch_student_specific_all_exam_info(student_id: str) -> List[StudentExamFeedback]:
    """
    Retrieve a student specific exam info document by exam_id and student_id identifiers.

    Returns
    -------
    List of QuestionAnswerFeedbackData
    """
    cursor = _student_col.find(
        {"student_id": student_id},
        {"_id": 0},  # hide internal Mongo ID
    )
    raw_feedbacks = []
    for doc in cursor:
        raw_feedbacks.extend(doc.get("student_exam_feedback", []))

    return [
        StudentExamFeedback.model_validate(feedback)
        for feedback in raw_feedbacks
    ]


def evaluation_data(grade: str, exam_type: str, course_name: str) -> EvaluationStat:
    """
    Retrieve how far the evaluation is done for a particular exam

    Returns
    -------
    EvaluationStat - An object consisting of evaluations_completed, evaluations_left, and list of student_ids whose evaluation is still left.
    """
    cursor = _student_col.find(
        {"exam_id": f"{grade}:{course_name}:{exam_type}"},
        {"_id": 0},  # hide internal Mongo ID
    )
    student_ids_left = []
    evaluations_completed = 0
    evaluations_left = 0
    for doc in cursor:
        if doc.get("evaluated"):
            evaluations_completed += 1
        else:
            student_ids_left.append(doc.get("student_id"))
            evaluations_left += 1

    return EvaluationStat(
        evaluations_completed=evaluations_completed,
        evaluations_left=evaluations_left,
        student_ids_left=student_ids_left
    )


def fetch_evaluation_feedback(grade: str, exam_type: str, course_name: str, student_id: str) -> List[QuestionAnswerFeedbackDataForInstructor]:

    doc = _student_col.find_one(
        {"exam_id": f"{grade}:{course_name}:{exam_type}", "student_id": student_id},
        {"_id": 0},  # hide internal Mongo ID
    )
    return [
        QuestionAnswerFeedbackDataForInstructor.model_validate(question_answer_feedback)
        for question_answer_feedback in doc.get("question_answer_feedback", [])
    ]


def mark_evaluated(grade: str, exam_type: str, course_name: str, student_id: str) -> int:

    result = _student_col.update_one(
        {"exam_id": f"{grade}:{course_name}:{exam_type}", "student_id": student_id},
        {"$set": {"evaluated": True}}
    )
    
    return result.modified_count


def fix_evaluated(grade: str, exam_type: str, course_name: str, student_id: str, exam_feedback: List[QuestionAnswerFeedbackDataForInstructor]) -> int:

    result = _student_col.update_one(
        {"exam_id": f"{grade}:{course_name}:{exam_type}", "student_id": student_id},
        {"$set": {"question_answer_feedback": exam_feedback}}
    )
    
    return result.modified_count