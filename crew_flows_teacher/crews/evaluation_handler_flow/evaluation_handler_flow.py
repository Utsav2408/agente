from datetime import datetime
from typing import List
from crewai.flow import Flow, start, listen
from crew_flows_teacher.crews.answer_key_handler_flow.answer_key_fix.fetch_question_number_crew.fetch_question_number_crew import FetchQuestionNumberCrew
from crew_flows_teacher.crews.evaluation_handler_flow.approve_evaluation_feedback_crew.approved_evaluation_feedback_crew import ApproveEvaluationFeedbackCrew
from crew_flows_teacher.crews.evaluation_handler_flow.evaluation_feedback_crew.evaluation_feedback_crew import EvaluationFeedbackCrew
from crew_flows_teacher.crews.evaluation_handler_flow.evaluation_handler_detail_crew.evaluation_handler_detail_crew import EvaluationHandlerDetailCrew
from crew_flows_teacher.crews.evaluation_handler_flow.evaluation_handler_intent_crew.evaluation_handler_intent_crew import EvaluatorIntentCrew
from crew_flows_teacher.crews.evaluation_handler_flow.fix_evaluation_feedback_crew.fix_evaluation_feedback_crew import FixEvaluationFeedbackCrew
from pydantic_models.crew_models import RoutingOutputTeacher
from pydantic_models.login_model import CustomMemoryTeacher, TurnTeacher
from logger.python_log import global_logger
from pydantic_models.student_exam_performance_models import FixEvaluationFeedback, QuestionAnswerFeedbackDataForInstructor
from routers.backend_job_routers.exam_data import evaluation_feedback_fix


class InstructorEvaluationFlow(Flow):
    def __init__(
        self,
        instructor_email: str,
        user_query: str,
        available_subject: List[str],
        custom_memory: CustomMemoryTeacher,
        supervisor_output: RoutingOutputTeacher
    ):
        super().__init__()
        self.instructor_email = instructor_email
        self.user_query = user_query
        self.available_subject = available_subject
        self.custom_memory = custom_memory
        self.supervisor_output = supervisor_output

    @start()
    def classify_intent(self) -> dict:
        payload = {
            "user_input": self.user_query,
            "conversation_history": self.custom_memory.model_dump_json(include=["conversation"]),
            "metadata": self.custom_memory.metadata.model_dump_json(include=["last_sub_route"])
        }
        global_logger.info("EvaluatorIntentCrew payload: %s", payload)
        try:
            res = EvaluatorIntentCrew().crew().kickoff(payload)
            intent_out = res.pydantic.model_dump()
        except Exception:
            global_logger.exception("EvaluatorIntentCrew failed, defaulting to fallback")
            intent_out = {"intent": "fallback"}
        global_logger.info("Intent classified as: %s", intent_out)
        return intent_out

    @listen(classify_intent)
    def handle_intent(self, intent_out: dict) -> str:
        try:
            intent = intent_out.get("sub_route")

            def safe_kickoff(crew_cls, payload, pydantic=False):
                global_logger.info("Payload for %s: %s", crew_cls.__name__, payload)
                try:
                    res = crew_cls().crew().kickoff(payload)
                    return res.pydantic if pydantic else res.raw
                except Exception as e:
                    global_logger.error("Error in %s", crew_cls.__name__, exc_info=True)
                    return None
            
            if intent == "evaluation_details":
                payload = {
                    "user_query": self.user_query,
                    "exam": self.custom_memory.metadata.last_exam,
                    "class": self.custom_memory.metadata.last_class,
                    "subject": self.custom_memory.metadata.last_subject,
                    "available_subjects": ', '.join(self.available_subject)
                }
                crew_response = safe_kickoff(EvaluationHandlerDetailCrew, payload, pydantic=True)
                bot_msg = crew_response.response \
                        or "I'm unable to fetch student's answer records. Please try again later or contact admin."
                
                self.custom_memory.metadata.last_exam = crew_response.evaluation_exam
                self.custom_memory.metadata.last_class = crew_response.evaluation_class
                self.custom_memory.metadata.last_subject = crew_response.evaluation_subject
                self.custom_memory.metadata.last_sub_route = intent

            elif intent == "evaluation_feedback":
                payload = {
                    "user_query": self.user_query,
                    "exam": self.custom_memory.metadata.last_exam,
                    "class": self.custom_memory.metadata.last_class,
                    "subject": self.custom_memory.metadata.last_subject,
                    "student_id": self.custom_memory.metadata.last_student_id
                }
                crew_response = safe_kickoff(EvaluationFeedbackCrew, payload, pydantic=True)

                if crew_response.student_id == "":
                    bot_msg = "Could you please share the student id for whom you want to evaluate ?"
                else:
                    suggested_evaluation_feedback_section = ""
                    for index, q_a_pair in enumerate(crew_response.suggested_evaluation_feedback_list):
                        suggested_evaluation_feedback_section += f"Question {str(index + 1)}: {q_a_pair.question} \n\n"
                        suggested_evaluation_feedback_section += f"Answer Key: {q_a_pair.answer_key} \n\n"
                        suggested_evaluation_feedback_section += f"Student Answer: {q_a_pair.student_answer} \n\n"
                        suggested_evaluation_feedback_section += f"Total Marks: {q_a_pair.total_mark} \n\n"
                        suggested_evaluation_feedback_section += f"Individual Mark: {q_a_pair.individual_mark} \n\n"
                        suggested_evaluation_feedback_section += f"Similarity Score: {q_a_pair.similarity_score} \n\n"
                        suggested_evaluation_feedback_section += f"Feedback: {q_a_pair.feedback} \n\n"
                    bot_msg = f"Following is the suggested evaluation for the student: \n\n {suggested_evaluation_feedback_section} Would you like to proceed with the above suggested evaluation ?"

                    self.custom_memory.metadata.last_evaluation_feedback_list = crew_response.suggested_evaluation_feedback_list
                    self.custom_memory.metadata.last_evaluation_feedback_section = suggested_evaluation_feedback_section
                    self.custom_memory.metadata.last_student_id = crew_response.student_id

                self.custom_memory.metadata.last_sub_route = intent

            elif intent == "approve_feedback":
                payload = {
                    "exam": self.custom_memory.metadata.last_exam,
                    "class": self.custom_memory.metadata.last_class,
                    "subject": self.custom_memory.metadata.last_subject,
                    "student_id": self.custom_memory.metadata.last_student_id
                }
                crew_response = safe_kickoff(ApproveEvaluationFeedbackCrew, payload, pydantic=True)

                bot_msg = crew_response.response \
                        or "I'm unable to submit student's evaluation feedback records. Please try again later or contact admin."  

                if crew_response.resolved:
                    evaluation_feedback_fix(FixEvaluationFeedback(
                        student_id=self.custom_memory.metadata.last_student_id,
                        grade=self.custom_memory.metadata.last_class,
                        course_name=self.custom_memory.metadata.last_subject,
                        exam_type=self.custom_memory.metadata.last_exam,
                        exam_feedback=self.custom_memory.metadata.last_evaluation_feedback_list
                    ))

                    self.custom_memory.metadata.last_evaluation_feedback_list = []
                    self.custom_memory.metadata.last_evaluation_feedback_section = ""
                    self.custom_memory.metadata.last_student_id = ""
                    self.custom_memory.metadata.last_question_discussed = 0

                self.custom_memory.metadata.last_sub_route = intent

            elif intent == "fix_feedback":
                if self.custom_memory.metadata.last_question_discussed == 0:
                    payload = {
                        "user_query": self.user_query
                    }
                    crew_response = safe_kickoff(FetchQuestionNumberCrew, payload, pydantic=True)
                    if crew_response.question_number == 0:
                        bot_msg = "Could you please mention the Question No. for which the changes are required ?"
                    else:
                        self.custom_memory.metadata.last_question_discussed = crew_response.question_number

                if self.custom_memory.metadata.last_question_discussed != 0:
                    bot_msg = ""
                    q_a_pair_needed = QuestionAnswerFeedbackDataForInstructor(
                        question="",
                        answer_key="",
                        student_answer="",
                        total_mark=0,
                        individual_mark=0,
                        similarity_score=0,
                        feedback=""
                    )
                    q_a_pair_needed = self.custom_memory.metadata.last_evaluation_feedback_list[self.custom_memory.metadata.last_question_discussed - 1]
                    payload = {
                        "user_input": self.user_query,
                        "individual_mark": q_a_pair_needed.individual_mark,
                        "similarity_score": q_a_pair_needed.similarity_score,
                        "feedback": q_a_pair_needed.feedback
                    }
                    crew_response = safe_kickoff(FixEvaluationFeedbackCrew, payload, pydantic=True)
                    q_a_pair_updated = []
                    for q_a_pair in self.custom_memory.metadata.last_evaluation_feedback_list:
                        if q_a_pair.question == q_a_pair_needed.question:
                            q_a_pair_updated.append(QuestionAnswerFeedbackDataForInstructor(
                                question=q_a_pair.question,
                                answer_key=q_a_pair.answer_key,
                                student_answer=q_a_pair.student_answer,
                                total_mark=q_a_pair.total_mark,
                                individual_mark=crew_response.individual_mark,
                                similarity_score=crew_response.similarity_score,
                                feedback=crew_response.feedback
                            ))
                        else:
                            q_a_pair_updated.append(q_a_pair)
                    self.custom_memory.metadata.last_evaluation_feedback_list = q_a_pair_updated
                    suggested_evaluation_feedback_section = ""
                    for index, q_a_pair in enumerate(self.custom_memory.metadata.last_evaluation_feedback_list):
                        suggested_evaluation_feedback_section += f"Question {str(index + 1)}: {q_a_pair.question} \n\n"
                        suggested_evaluation_feedback_section += f"Answer Key: {q_a_pair.answer_key} \n\n"
                        suggested_evaluation_feedback_section += f"Student Answer: {q_a_pair.student_answer} \n\n"
                        suggested_evaluation_feedback_section += f"Total Marks: {q_a_pair.total_mark} \n\n"
                        suggested_evaluation_feedback_section += f"Individual Mark: {q_a_pair.individual_mark} \n\n"
                        suggested_evaluation_feedback_section += f"Similarity Score: {q_a_pair.similarity_score} \n\n"
                        suggested_evaluation_feedback_section += f"Feedback: {q_a_pair.feedback} \n\n"
                    bot_msg = f"Following is the updated evaluation for the student: \n\n {suggested_evaluation_feedback_section} Would you like to proceed with the above suggested evaluation ?"
                    self.custom_memory.metadata.last_evaluation_feedback_section = suggested_evaluation_feedback_section     

                self.custom_memory.metadata.last_sub_route = intent
            else:
                bot_msg = "I'm not sure how to help with that—could you rephrase?"
            
            # record bot turn
            self.custom_memory.conversation.append(
                TurnTeacher(
                    sender="bot", 
                    message=bot_msg, 
                    timestamp=datetime.now(),
                    route=self.supervisor_output.route,
                    reason=self.supervisor_output.reason,
                    sub_route=intent
                )
            )
            return bot_msg
        except Exception as e:
            print(e)
            raise e


async def kickoff(
    instructor_email: str,
    user_query: str,
    custom_memory: CustomMemoryTeacher,
    supervisor_output: RoutingOutputTeacher,
    available_subject: List[str]
) -> str:
    try:
        instructor_evaluation_flow = InstructorEvaluationFlow(
            instructor_email = instructor_email,
            user_query = user_query,
            custom_memory = custom_memory,
            supervisor_output = supervisor_output,
            available_subject = available_subject
        )
        return await instructor_evaluation_flow.kickoff_async()
    except Exception as e:
        raise e