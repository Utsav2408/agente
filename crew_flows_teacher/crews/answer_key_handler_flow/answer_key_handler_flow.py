from datetime import datetime
from typing import List
from crewai.flow import Flow, start, listen
from crew_flows_teacher.crews.answer_key_handler_flow.answer_key_approve.answer_key_approve_crew import ApproveAnswerKeyCrew
from crew_flows_teacher.crews.answer_key_handler_flow.answer_key_details.answer_key_detail_crew import AnswerKeyDetailCrew
from crew_flows_teacher.crews.answer_key_handler_flow.answer_key_fix.answer_key_fix_crew import FixAnswerKeyCrew
from crew_flows_teacher.crews.answer_key_handler_flow.answer_key_fix.fetch_question_number_crew.fetch_question_number_crew import FetchQuestionNumberCrew
from crew_flows_teacher.crews.answer_key_handler_flow.answer_key_handler_intent.answer_key_handler_crew import AnswerKeyIntentCrew
from pydantic_models.crew_models import RoutingOutputTeacher
from pydantic_models.exam_models import FixAnswerKeyRequest, QuestionAnswerData
from pydantic_models.login_model import CustomMemoryTeacher, TurnTeacher
from logger.python_log import global_logger
from routers.backend_job_routers.exam_data import fix_answer_keys


class InstructorAnswerKeyFlow(Flow):
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
        global_logger.info("AnswerKeyIntentCrew payload: %s", payload)
        try:
            res = AnswerKeyIntentCrew().crew().kickoff(payload)
            intent_out = res.pydantic.model_dump()
        except Exception:
            global_logger.exception("AnswerKeyIntentCrew failed, defaulting to fallback")
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
            
            if intent == "answer_key_details":
                payload = {
                    "user_query": self.user_query,
                    "exam": self.custom_memory.metadata.last_exam,
                    "class": self.custom_memory.metadata.last_class,
                    "subject": self.custom_memory.metadata.last_subject,
                    "available_subjects": ', '.join(self.available_subject)
                }
                crew_response = safe_kickoff(AnswerKeyDetailCrew, payload, pydantic=True)
                if 'response' in crew_response.__pydantic_fields_set__:
                    bot_msg = crew_response.response \
                            or "I'm unable to fetch answer keys for the exam. Please try again later or contact admin."
                else:
                    generated_answer_key = ""
                    for index, q_a_pair in enumerate(crew_response.generated_answer_key_list):
                        generated_answer_key += f"Question {str(index + 1)}: {q_a_pair.question} \n\n"
                        generated_answer_key += f"Answer: {q_a_pair.answer} \n\n"
                        generated_answer_key += f"Total Marks: {q_a_pair.total_mark} \n\n"
                    bot_msg = f"Following is the suggested answer key: \n\n {generated_answer_key} Would you like to proceed with the above generated answer key ?"
                
                if crew_response.answer_key_exam != "" and crew_response.answer_key_class != "" and crew_response.answer_key_subject != "":
                    self.custom_memory.metadata.last_generated_answer_key = generated_answer_key
                    self.custom_memory.metadata.generated_answer_key_list = crew_response.generated_answer_key_list

                self.custom_memory.metadata.last_exam = crew_response.answer_key_exam
                self.custom_memory.metadata.last_class = crew_response.answer_key_class
                self.custom_memory.metadata.last_subject = crew_response.answer_key_subject
                self.custom_memory.metadata.last_sub_route = intent

            elif intent == "approve_answer_key":
                payload = {
                    "exam": self.custom_memory.metadata.last_exam,
                    "class": self.custom_memory.metadata.last_class,
                    "subject": self.custom_memory.metadata.last_subject
                }
                crew_response = safe_kickoff(ApproveAnswerKeyCrew, payload, pydantic=True)

                bot_msg = crew_response.response \
                        or "I'm unable to submit student's evaluation feedback records. Please try again later or contact admin."  

                if crew_response.resolved:
                    fix_answer_keys(FixAnswerKeyRequest(
                        grade = self.custom_memory.metadata.last_class,
                        exam_type = self.custom_memory.metadata.last_exam,
                        course_name = self.custom_memory.metadata.last_subject,
                        question_answer = self.custom_memory.metadata.generated_answer_key_list
                    ))

                    self.custom_memory.metadata.last_generated_answer_key = ""
                    self.custom_memory.metadata.generated_answer_key_list = []
                    self.custom_memory.metadata.last_question_discussed = 0

                self.custom_memory.metadata.last_sub_route = intent

            elif intent == "fix_answer_key":
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
                    q_a_pair_needed = QuestionAnswerData(
                        question="",
                        total_mark=0,
                        answer=""
                    )
                    q_a_pair_needed = self.custom_memory.metadata.generated_answer_key_list[self.custom_memory.metadata.last_question_discussed - 1]
                    payload = {
                        "user_input": self.user_query,
                        "answer": q_a_pair_needed.answer,
                        "question": q_a_pair_needed.question,
                        "marks": q_a_pair_needed.total_mark
                    }
                    crew_response = safe_kickoff(FixAnswerKeyCrew, payload, pydantic=True)
                    q_a_pair_updated = []
                    for q_a_pair in self.custom_memory.metadata.generated_answer_key_list:
                        if q_a_pair.question == q_a_pair_needed.question:
                            q_a_pair_updated.append(QuestionAnswerData(
                                question=q_a_pair.question,
                                answer=crew_response.updated_answer,
                                total_mark=q_a_pair.total_mark
                            ))
                        else:
                            q_a_pair_updated.append(q_a_pair)
                    self.custom_memory.metadata.generated_answer_key_list = q_a_pair_updated
                    generated_answer_key = ""
                    for index, q_a_pair in enumerate(self.custom_memory.metadata.generated_answer_key_list):
                        generated_answer_key += f"Question {str(index + 1)}: {q_a_pair.question} \n\n"
                        generated_answer_key += f"Answer: {q_a_pair.answer} \n\n"
                        generated_answer_key += f"Total Marks: {q_a_pair.total_mark} \n\n"
                    bot_msg = f"Following is the updated answer key: \n\n {generated_answer_key} Would you like to proceed with the above generated answer key ?"
                    self.custom_memory.metadata.last_generated_answer_key = generated_answer_key     

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
            raise e


async def kickoff(
    instructor_email: str,
    user_query: str,
    custom_memory: CustomMemoryTeacher,
    supervisor_output: RoutingOutputTeacher,
    available_subject: List[str]
) -> str:
    try:
        instructor_answer_key_flow = InstructorAnswerKeyFlow(
            instructor_email = instructor_email,
            user_query = user_query,
            custom_memory = custom_memory,
            supervisor_output = supervisor_output,
            available_subject=available_subject
        )
        return await instructor_answer_key_flow.kickoff_async()
    except Exception as e:
        raise e