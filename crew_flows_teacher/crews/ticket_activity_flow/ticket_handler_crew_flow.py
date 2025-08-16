from datetime import datetime
from crewai.flow import Flow, start, listen
from crew_flows_teacher.crews.ticket_activity_flow.approve_suggestion_crew.approved_resolution_crew import ApproveSuggestionCrew
from crew_flows_teacher.crews.ticket_activity_flow.fix_suggestion_crew.fix_suggestion_crew import FixSuggestionCrew
from crew_flows_teacher.crews.ticket_activity_flow.resolve_ticket_flow.resolve_ticket_crew.resolve_ticket_crew import ResolveTicketCrew
from crew_flows_teacher.crews.ticket_activity_flow.support_ticket_detail_crew.support_ticket_detail_crew import SupportTicketDetailCrew
from crew_flows_teacher.crews.ticket_activity_flow.ticket_handler_intent_crew.ticket_handler_intent_crew import TicketHandlerIntentCrew
from pydantic_models.crew_models import RoutingOutputTeacher
from pydantic_models.login_model import CustomMemoryTeacher, TurnTeacher
from logger.python_log import global_logger


class InstructorTicketHandlerFlow(Flow):
    def __init__(
        self,
        instructor_id: str,
        instructor_email: str,
        user_query: str,
        custom_memory: CustomMemoryTeacher,
        supervisor_output: RoutingOutputTeacher
    ):
        super().__init__()
        self.instructor_id = instructor_id
        self.instructor_email = instructor_email
        self.user_query = user_query
        self.custom_memory = custom_memory
        self.supervisor_output = supervisor_output

    @start()
    def classify_intent(self) -> dict:
        payload = {
            "user_input": self.user_query,
            "conversation_history": self.custom_memory.model_dump_json(include=["conversation"]),
            "metadata": self.custom_memory.model_dump_json(include=["metadata"])
        }
        global_logger.info("TicketHandlerIntentCrew payload: %s", payload)
        try:
            res = TicketHandlerIntentCrew().crew().kickoff(payload)
            intent_out = res.pydantic.model_dump()
        except Exception:
            global_logger.exception("TicketHandlerIntentCrew failed, defaulting to fallback")
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

            if intent == "support_ticket_detail":
                payload = {
                    "user_query": self.user_query,
                    "metadata": self.custom_memory.model_dump_json(include=["metadata"]),
                    "instructor_id": self.instructor_id,
                    "instructor_email": self.instructor_email
                }
                crew_response = safe_kickoff(SupportTicketDetailCrew, payload, pydantic=True)
                bot_msg = crew_response.response \
                        or "I'm unable to fetch your support ticket records. Please try again later or contact admin."
                if crew_response.support_ticket_id != "":
                    self.custom_memory.metadata.last_support_ticket = crew_response.support_ticket_id
                self.custom_memory.metadata.last_sub_route = intent

            elif intent == "resolve_ticket":
                payload = {
                    "user_query": self.user_query,
                    "last_support_ticket_id": self.custom_memory.metadata.last_support_ticket,
                    "support_ticket_id": self.custom_memory.metadata.last_support_ticket
                }
                crew_response = safe_kickoff(ResolveTicketCrew, payload, pydantic=True)
                if crew_response.support_ticket_id != "":
                    bot_msg = crew_response.response \
                            or "I'm unable to work on your ticket right now. Please try again later or contact admin."
                    self.custom_memory.metadata.last_support_ticket = crew_response.support_ticket_id
                    self.custom_memory.metadata.assignee_reply = crew_response.suggested_reply
                else:
                    bot_msg = "Could you please provide the support ticket id which you would like to resolve?"

                self.custom_memory.metadata.last_sub_route = intent

            elif intent == "approve_suggestion":
                payload = {
                    "support_ticket_id": self.custom_memory.metadata.last_support_ticket,
                    "support_ticket_reply": self.custom_memory.metadata.assignee_reply
                }                
                crew_response = safe_kickoff(ApproveSuggestionCrew, payload, pydantic=True)
                bot_msg = crew_response.response \
                        or "I'm unable to resolve your ticket right now. Please try again later or contact admin."
                
                if crew_response.resolved:
                    self.custom_memory.metadata.last_support_ticket = ""
                    self.custom_memory.metadata.assignee_reply = ""
                self.custom_memory.metadata.last_sub_route = intent

            elif intent == "fix_suggestion":
                payload = {
                    "user_input": self.user_query,
                    "suggested_reply": self.custom_memory.metadata.assignee_reply
                }
                crew_response = safe_kickoff(FixSuggestionCrew, payload, pydantic=True)
                bot_msg = crew_response.response \
                        or "I'm unable to update the suggested reply with your suggestion. Please try again later or contact admin."
                
                if crew_response.suggested_reply != "":
                    self.custom_memory.metadata.assignee_reply = crew_response.suggested_reply
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
    instructor_id: str,
    instructor_email: str,
    user_query: str,
    custom_memory: CustomMemoryTeacher,
    supervisor_output: RoutingOutputTeacher

) -> str:
    try:
        instructor_ticket_handler_flow = InstructorTicketHandlerFlow(
            instructor_id = instructor_id,
            instructor_email = instructor_email,
            user_query = user_query,
            custom_memory = custom_memory,
            supervisor_output = supervisor_output
        )
        return await instructor_ticket_handler_flow.kickoff_async()
    except Exception as e:
        raise e