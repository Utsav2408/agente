from typing import List
from mongo_ops import exam_data, course_data, student_performance_data
from pydantic_models.student_exam_performance_models import QuestionAnswerFeedbackData, StudentExamPerformance, StudentExamRequest, StudentPerformanceRequest


def fetch_student_all_exam_performance(student_data: StudentPerformanceRequest) -> List[StudentExamPerformance]:
    try:
        student_exam_feedbacks = student_performance_data.fetch_student_specific_all_exam_info(
            student_id=student_data.student_id
        )

        all_exam_performance: List[StudentExamPerformance] = []
        for exam_feedback in student_exam_feedbacks:
            exam_info = exam_data.get_exam_by_id(exam_feedback.exam_id)
            course_info = course_data.get_course_by_id(exam_info.course_id)
            all_exam_performance.append(StudentExamPerformance(
                course_name=course_info.course_name,
                exam_type=exam_info.exam_type,
                stats=exam_info.stats,
                exam_feedback=exam_feedback.question_answer_feedback
            ))
        return all_exam_performance
    except Exception as e:
        raise e


def fetch_student_exam_record(student_data: StudentExamRequest) -> List[QuestionAnswerFeedbackData]:
    try:
        exam_id = f"{student_data.grade}:{student_data.course_name.lower().replace(' ', '_')}:{student_data.exam_type}"
        return student_performance_data.fetch_student_specific_exam_info(
            exam_id=exam_id,
            student_id=student_data.student_id
        )
    except Exception as e:
        raise e

