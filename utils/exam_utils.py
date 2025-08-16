from typing import List
from crew_flows_teacher.crews.answer_key_handler_flow.generate_answer.generate_answer_crew import GenerateAnswerCrew
from crew_flows_teacher.crews.evaluation_handler_flow.evaluate_student_answer.evaluate_student_answer_crew import EvaluateStudentAnswerCrew
from document_processing.embedding import paragraph_similarity_pct
from pydantic_models.exam_models import ExamDataSpec, ExamData, ExamStat, QuestionAnswerData
from mongo_ops import exam_data, course_data, grade_data, student_performance_data
from pydantic_models.student_exam_performance_models import QuestionAnswerFeedbackDataForInstructor, StudentExamFeedback, StudentExamSpecificAddDataRequest


def add_exam(exam_config: ExamDataSpec):
    try:
        course = course_data.get_course_by_name(exam_config.course_name)
        grade = grade_data.get_grade_data(exam_config.grade)
        question_answer_data: List[QuestionAnswerData] = []
        for q in exam_config.questions:
            payload = {
                "question": q.question,
                "available_subjects": [mapping.course_name for mapping in grade.mapping],
                "marks": q.total_mark,
                "grade": exam_config.grade,
                "previous_answer": ""
            }
            question_answer_data.append(QuestionAnswerData(
                question=q.question,
                total_mark=q.total_mark,
                answer=GenerateAnswerCrew().crew().kickoff(payload).pydantic.response
            ))

        exam = ExamData(
            exam_id=f"{exam_config.grade}:{course.course_id}:{exam_config.exam_type}",
            grade=exam_config.grade,
            exam_type=exam_config.exam_type,
            course_id=course.course_id,
            question_answer=question_answer_data,
            explored=False,
            stats=ExamStat(
                total_marks=exam_config.exam_marks,
                highest=0,
                lowest=0,
                pass_percentage=0
            )
        )
        exam_data.add_exam(exam)
    except Exception as e:
        raise e


def add_student_answers(performance_config: StudentExamSpecificAddDataRequest):
    try:
        course = course_data.get_course_by_name(performance_config.course_name)
        exam = exam_data.get_exam_by_keys(performance_config.exam_type, course.course_id)

        for performance in performance_config.data:
            question_answer: List[QuestionAnswerFeedbackDataForInstructor] = []
            for exam_question_answer in performance.question_answer:

                answer = next(
                    (qa.answer for qa in exam.question_answer
                    if qa.question == exam_question_answer.question),
                    None
                )

                total_marks = next(
                    (qa.total_mark for qa in exam.question_answer
                    if qa.question == exam_question_answer.question),
                    None
                )

                payload = {
                    "question": exam_question_answer.question,
                    "student_answer": exam_question_answer.answer,
                    "answer_key": answer,
                    "total_marks": total_marks
                }
                evaluation = EvaluateStudentAnswerCrew().crew().kickoff(payload).pydantic

                question_answer.append(QuestionAnswerFeedbackDataForInstructor(
                    question=exam_question_answer.question,
                    answer_key=answer,
                    student_answer=exam_question_answer.answer,
                    total_mark=total_marks,
                    individual_mark=evaluation.marks,
                    similarity_score=paragraph_similarity_pct(exam_question_answer.answer, answer),
                    feedback=evaluation.feedback
                ))
            
            
            student_performance_data.add_student_specific_exam_info(StudentExamFeedback(
                exam_id=exam.exam_id,
                student_id=performance.student_id,
                question_answer_feedback=question_answer,
                evaluated=False
            ))

    except Exception as e:
        raise e