from datetime import datetime
from crewai.flow import Flow, start, listen
from crew_flows_teacher.crews.ticket_activity_flow.resolve_ticket_flow.resolve_course_query_crew.resolve_course_query import ResolveCourseQuery
from mongo_ops import student_data
from mongo_ops.support_ticket_data import get_support_ticket_by_id, update_suggested_reply
from pydantic_models.login_model import CustomMemory, Turn
from crew_flows_student.crews.support_crew_flow.support_ticket_prompt_crew.support_ticket_prompt_crew import SupportTicketPromptCrew
from crew_flows_student.crews.support_crew_flow.raise_ticket_crew.raise_ticket_crew import RaiseTicketCrew
from crew_flows_student.crews.support_crew_flow.fetch_ticket_crew.fetch_ticket_crew import FetchTicketCrew
from crew_flows_student.crews.support_crew_flow.administrative_query_crew.administrative_query_crew import AdministrativeQueryCrew
from crew_flows_student.crews.support_crew_flow.support_intent_crew.support_intent_crew import SupportIntentCrew
from logger.python_log import global_logger


import asyncio
import threading

# --- helper: run the heavy "suggested reply" generation off-thread/loop ---
async def _compute_and_persist_suggested_reply(ticket, student):
    """
    Branch on ticket type, run the blocking crew calls in a worker thread,
    then persist the result without blocking the caller.
    """
    # Build payloads in the main thread (cheap)
    if ticket.support_type == "course":
        payload = {
            "support_ticket_issue": ticket.support_content,
            "available_subjects": student.course_names,
            "grade": student.grade,
        }
        # Offload blocking call to a thread:
        suggested_reply = await asyncio.to_thread(
            lambda: ResolveCourseQuery().crew().kickoff(payload).pydantic.response
        )
    else:
        payload = {"user_input": ticket.support_content}
        suggested_reply = await asyncio.to_thread(
            lambda: AdministrativeQueryCrew().crew().kickoff(payload).pydantic.response
        )

    # Persist in the background too (in case it's blocking/DB-bound)
    await asyncio.to_thread(update_suggested_reply, ticket.support_ticket_id, suggested_reply)


def _spawn_background_task(coro):
    """Create the background task whether or not we're inside a running loop."""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(coro)  # schedule and return immediately
    except RuntimeError:
        # No running loop (likely sync context). Start a lightweight loop in a daemon thread.
        def _runner():
            asyncio.run(coro)
        threading.Thread(target=_runner, name="suggested-reply-worker", daemon=True).start()


class StudentSupportFlow(Flow):
    def __init__(
        self,
        student_id: str,
        user_query: str,
        custom_memory: CustomMemory
    ):
        super().__init__()
        self.student_id = student_id
        self.user_query = user_query
        self.custom_memory = custom_memory

    @start()
    def classify_intent(self) -> dict:
        payload = {
            "user_input": self.user_query,
            "conversation_history": self.custom_memory.model_dump_json(),
            "student_id": self.student_id
        }
        global_logger.info("SupportIntentCrew payload: %s", payload)
        try:
            res = SupportIntentCrew().crew().kickoff(payload)
            intent_out = res.pydantic.model_dump()
        except Exception:
            global_logger.exception("SupportIntentCrew failed, defaulting to escalation")
            intent_out = {"intent": "escalation"}
        global_logger.info("Intent classified as: %s", intent_out)
        return intent_out

    @listen(classify_intent)
    def handle_intent(self, intent_out: dict) -> str:
        try:
            intent = intent_out.get("intent")
            payload = {
                "user_input": self.user_query,
                "conversation_history": self.custom_memory.model_dump_json(),
                "student_id": self.student_id
            }

            def safe_kickoff(crew_cls, payload, pydantic=False):
                global_logger.info("Payload for %s: %s", crew_cls.__name__, payload)
                try:
                    res = crew_cls().crew().kickoff(payload)
                    return res.pydantic if pydantic else res.raw
                except Exception as e:
                    global_logger.error("Error in %s", crew_cls.__name__, exc_info=True)
                    return None

            # 1) Escalation → delegate to SupportTicketPromptCrew
            if intent == "escalation":
                bot_msg = safe_kickoff(SupportTicketPromptCrew, payload) \
                        or "Would you like me to raise a support ticket for this?"

            # 2) Ticket creation → call RaiseTicketCrew
            elif intent == "ticket_creation":
                crew_response = safe_kickoff(RaiseTicketCrew, payload, pydantic=True)
                bot_msg = crew_response.response \
                        or "Failed to create support ticket. Please try again later or contact admin."
                
                ticket = get_support_ticket_by_id(crew_response.support_ticket_id)
                student = student_data.get_student_public(
                    student_id=self.student_id
                )

                _spawn_background_task(_compute_and_persist_suggested_reply(ticket, student))

            # elif intent == "ticket_creation":
            #     crew_response = safe_kickoff(RaiseTicketCrew, payload, pydantic=True)
            #     bot_msg = crew_response.response \
            #             or "Failed to create support ticket. Please try again later or contact admin."
                
            #     ticket = get_support_ticket_by_id(crew_response.support_ticket_id)
            #     student = student_data.get_student_public(
            #             student_id=self.student_id
            #         )
            #     suggested_reply = ""
            #     if ticket.support_type == "course":
            #         payload = {
            #             "support_ticket_issue": ticket.support_content,
            #             "available_subjects": student.course_names,
            #             "grade": student.grade
            #         }
            #         suggested_reply = ResolveCourseQuery().crew().kickoff(payload).pydantic.response
            #     else:
            #         payload = {
            #             "user_input": ticket.support_content
            #         }
            #         suggested_reply = AdministrativeQueryCrew().crew().kickoff(payload).pydantic.response
                
            #     update_suggested_reply(ticket.support_ticket_id, suggested_reply)

            # 3) Ticket details → call FetchTicketCrew
            elif intent == "ticket_details":
                bot_msg = safe_kickoff(FetchTicketCrew, payload) \
                        or "Sorry, I couldn't fetch your ticket details right now."

            # 4) Administrative query → call AdministrativeQueryCrew
            elif intent == "administrative_query":
                bot_msg = safe_kickoff(AdministrativeQueryCrew, payload, pydantic=True).response \
                        or "Sorry, I couldn't retrieve that information right now."

            # 5) Fallback
            else:
                bot_msg = "I'm not sure how to help with that—could you rephrase?"

            # record bot turn
            self.custom_memory.conversation.append(
                Turn(sender="bot", message=bot_msg, timestamp=datetime.now())
            )
            return bot_msg
        except Exception as e:
            print(e)
            raise e


async def kickoff(
    student_id: str,
    user_query: str,
    custom_memory: CustomMemory
) -> str:
    try:
        student_support_flow = StudentSupportFlow(
            student_id= student_id,
            user_query= user_query,
            custom_memory= custom_memory
        )
        return await student_support_flow.kickoff_async()
    except Exception as e:
        print(e)
        raise e