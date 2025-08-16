from datetime import datetime
from crewai.flow import Flow, start, listen
from crew_flows_teacher.crews.announcement_flow.announcement_approve_crew.announcement_approve_crew import ApproveSuggestionCrew
from crew_flows_teacher.crews.announcement_flow.announcement_creator_crew.announcement_creator_crew import AnnouncementCreatorCrew
from crew_flows_teacher.crews.announcement_flow.announcement_detail_crew.announcement_detail_crew import AnnouncementDetailCrew
from crew_flows_teacher.crews.announcement_flow.announcement_fix_crew.announcement_fix_crew import AnnouncementFixCrew
from crew_flows_teacher.crews.announcement_flow.announcement_intent_crew.announcement_intent_crew import AnnouncementIntentCrew
from pydantic_models.crew_models import RoutingOutputTeacher
from pydantic_models.login_model import CustomMemoryTeacher, TurnTeacher
from logger.python_log import global_logger


class InstructorAnnouncementFlow(Flow):
    def __init__(
        self,
        instructor_email: str,
        user_query: str,
        custom_memory: CustomMemoryTeacher,
        supervisor_output: RoutingOutputTeacher
    ):
        super().__init__()
        self.instructor_email = instructor_email
        self.user_query = user_query
        self.custom_memory = custom_memory
        self.supervisor_output = supervisor_output

    @start()
    def classify_intent(self) -> dict:
        payload = {
            "user_input": self.user_query,
            "conversation_history": self.custom_memory.model_dump_json(include=["conversation"]),
            "metadata": self.custom_memory.metadata.model_dump_json(include=["last_announcement_id", "last_sub_route"])
        }
        global_logger.info("AnnouncementIntentCrew payload: %s", payload)
        try:
            res = AnnouncementIntentCrew().crew().kickoff(payload)
            intent_out = res.pydantic.model_dump()
        except Exception:
            global_logger.exception("AnnouncementIntentCrew failed, defaulting to fallback")
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

            if intent == "announcement_detail":
                payload = {
                    "user_query": self.user_query,
                    "metadata": self.custom_memory.metadata.model_dump_json(include=["last_announcement_id", "last_sub_route"]),
                    "instructor_email": self.instructor_email
                }
                crew_response = safe_kickoff(AnnouncementDetailCrew, payload, pydantic=True)
                bot_msg = crew_response.response \
                        or "I'm unable to fetch your announcement records. Please try again later or contact admin."
                if crew_response.announcement_id != "":
                    self.custom_memory.metadata.last_announcement_id = crew_response.announcement_id
                self.custom_memory.metadata.last_sub_route = intent

            elif intent == "announcement_creator":
                payload = {
                    "user_query": self.user_query,
                    "last_announcement_class": self.custom_memory.metadata.last_announcement_class,
                    "last_announcement_summary": self.custom_memory.metadata.last_announcement_summary,
                    "last_announcement_event_date": self.custom_memory.metadata.last_announcement_event_date
                }
                crew_response = safe_kickoff(AnnouncementCreatorCrew, payload, pydantic=True)

                if 'response' in crew_response.__pydantic_fields_set__:
                    bot_msg = crew_response.response \
                            or "I'm facing difficulties in creating announcement. Please try again later or contact admin."
                else:
                    bot_msg = f"I hope you find this draft suitable for your announcement. \n\nTitle of Announcement: {crew_response.announcement_title} \n\nAnnouncement Class: {crew_response.announcement_class} \n\nAnnouncement Body: {crew_response.draft_announcement} \n\nEvent Date: {crew_response.announcement_event_date} \n\nWould you like to publish this suggested draft?"
                
                if crew_response.announcement_class != "" and crew_response.announcement_summary != "" and crew_response.announcement_event_date != "":
                    self.custom_memory.metadata.last_draft_announcement = crew_response.draft_announcement
                    self.custom_memory.metadata.last_announcement_title = crew_response.announcement_title
                if crew_response.announcement_class != "":
                    self.custom_memory.metadata.last_announcement_class = crew_response.announcement_class
                if crew_response.announcement_summary != "":
                    self.custom_memory.metadata.last_announcement_summary = crew_response.announcement_summary
                if crew_response.announcement_event_date != "":
                    self.custom_memory.metadata.last_announcement_event_date = crew_response.announcement_event_date

                self.custom_memory.metadata.last_sub_route = intent

            elif intent == "announcement_approved":
                payload = {
                    "announcement_class": self.custom_memory.metadata.last_announcement_class,
                    "instructor_email": self.instructor_email,
                    "announcement_title": self.custom_memory.metadata.last_announcement_title,
                    "announcement_content": self.custom_memory.metadata.last_draft_announcement,
                    "announcement_event_date": self.custom_memory.metadata.last_announcement_event_date
                }
                crew_response = safe_kickoff(ApproveSuggestionCrew, payload, pydantic=True)
                bot_msg = crew_response.response \
                        or "I'm facing difficulties in creating announcement. Please try again later or contact admin."
                if crew_response.resolved:
                    self.custom_memory.metadata.last_announcement_id = crew_response.announcement_id
                    self.custom_memory.metadata.last_announcement_class = ""
                    self.custom_memory.metadata.last_announcement_event_date = ""
                    self.custom_memory.metadata.last_announcement_summary = ""
                    self.custom_memory.metadata.last_draft_announcement = ""
                    self.custom_memory.metadata.last_announcement_title = ""

                self.custom_memory.metadata.last_sub_route = intent
            elif intent == "announcement_fix":
                payload = {
                    "user_input": self.user_query,
                    "announcement_title": self.custom_memory.metadata.last_announcement_title,
                    "announcement_class": self.custom_memory.metadata.last_announcement_class,
                    "announcement_summary": self.custom_memory.metadata.last_announcement_summary,
                    "announcement_event_date": self.custom_memory.metadata.last_announcement_event_date,
                    "draft_announcement": self.custom_memory.metadata.last_draft_announcement
                }
                crew_response = safe_kickoff(AnnouncementFixCrew, payload, pydantic=True)

                if 'response' in crew_response.__pydantic_fields_set__:
                    bot_msg = crew_response.response \
                            or "I'm unable to fix your announcement. Please try again later or contact admin."
                else:
                    bot_msg = f"The suggested draft announcement has been updated based on your inputs. \n\nUpdated Draft Announcement \n\nTitle of Announcement: {crew_response.announcement_title} \n\nAnnouncement Class: {crew_response.announcement_class} \n\nAnnouncement Body: {crew_response.draft_announcement} \n\nEvent Date: {crew_response.announcement_event_date} \n\nDo you want to publish this updated draft announcement?"
                
                self.custom_memory.metadata.last_announcement_title = crew_response.announcement_title
                self.custom_memory.metadata.last_announcement_class = crew_response.announcement_class
                self.custom_memory.metadata.last_announcement_summary = crew_response.announcement_summary
                self.custom_memory.metadata.last_announcement_event_date = crew_response.announcement_event_date                
                self.custom_memory.metadata.last_draft_announcement = crew_response.draft_announcement
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
    supervisor_output: RoutingOutputTeacher

) -> str:
    try:
        instructor_announcement_flow = InstructorAnnouncementFlow(
            instructor_email = instructor_email,
            user_query = user_query,
            custom_memory = custom_memory,
            supervisor_output = supervisor_output
        )
        return await instructor_announcement_flow.kickoff_async()
    except Exception as e:
        print(e)
        raise e