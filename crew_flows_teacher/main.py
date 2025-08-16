from datetime import datetime
from typing import List
from crewai.flow import Flow, listen, start
from crew_flows_teacher.crews.evaluation_handler_flow import evaluation_handler_flow
from crew_flows_teacher.crews.answer_key_handler_flow import answer_key_handler_flow
from crew_flows_teacher.crews.supervisor_crew_teacher.supervisor_teacher import SupervisorTeacherCrew, RoutingOutputTeacher
from crew_flows_teacher.crews.ticket_activity_flow import ticket_handler_crew_flow
from crew_flows_teacher.crews.announcement_flow import announcement_flow
from pydantic_models.login_model import CustomMemoryTeacher, TurnTeacher
from redis_db.redis_client import redis_client
from logger.python_log import global_logger

import mlflow

mlflow.crewai.autolog()

class InstructorAgentFlow(Flow):
    def __init__(
        self,
        instructor_id: str,
        instructor_email: str,
        user_query: str,
        custom_memory: CustomMemoryTeacher,
        available_subject: List[str]
    ):
        super().__init__()
        self.instructor_id = instructor_id
        self.instructor_email = instructor_email
        self.user_query = user_query
        self.custom_memory = custom_memory
        self.available_subject = available_subject

    @start()
    async def supervisor(self):
        # Prepare payload
        sup_payload = {
            "user_input": self.user_query,
            "conversation_history": self.custom_memory.model_dump_json(include=["conversation"])
        }
        global_logger.info("Supervisor payload: %s", sup_payload)

        # Call supervisor crew with error handling
        try:
            raw_res = SupervisorTeacherCrew().crew().kickoff(sup_payload)
            pyd_res: RoutingOutputTeacher = raw_res.pydantic
        except Exception as e:
            global_logger.error("SupervisorTeacherCrew kickoff error", exc_info=True)

        routing = pyd_res.model_dump()
        global_logger.info("Routing decision: %s", routing)
        return pyd_res

    @listen(supervisor)
    async def call_crew(self, supervisor_output: RoutingOutputTeacher):
        route = supervisor_output.route
        reason = supervisor_output.reason
        global_logger.info("Handling route '%s' with reason '%s'", route, reason)

        # Record the user message
        self.custom_memory.conversation.append(
            TurnTeacher(
                sender="user", 
                message=self.user_query, 
                timestamp=datetime.now()
            )
        )

        # Helper for error-handled kickoff
        def safe_kickoff(crew_cls, payload, pydantic=False):
            global_logger.info("Payload for %s: %s", crew_cls.__name__, payload)
            try:
                res = crew_cls().crew().kickoff(payload)
                return res.pydantic if pydantic else res.raw
            except Exception as e:
                global_logger.error("Error in %s", crew_cls.__name__, exc_info=True)
                return None

        if route == "ticket_activity":
            result = await ticket_handler_crew_flow.kickoff(
                instructor_id=self.instructor_id,
                instructor_email=self.instructor_email,
                user_query=self.user_query,
                custom_memory=self.custom_memory,
                supervisor_output=supervisor_output
            )
            bot_response = result or "Sorry, I'm facing some issues while processing your request. Please try again later."
            return bot_response
        
        elif route == "announcement_activity":
            result = await announcement_flow.kickoff(
                instructor_email=self.instructor_email,
                user_query=self.user_query,
                custom_memory=self.custom_memory,
                supervisor_output=supervisor_output
            )
            bot_response = result or "Sorry, I'm facing some issues while processing your request. Please try again later."
            return bot_response     

        elif route == "evaluation_activity":
            result = await evaluation_handler_flow.kickoff(
                instructor_email=self.instructor_email,
                user_query=self.user_query,
                custom_memory=self.custom_memory,
                supervisor_output=supervisor_output,
                available_subject=self.available_subject
            )
            bot_response = result or "Sorry, I'm facing some issues while processing your request. Please try again later."   
            return bot_response     

        elif route == "answer_key_generation_activity":
            result = await answer_key_handler_flow.kickoff(
                instructor_email=self.instructor_email,
                user_query=self.user_query,
                custom_memory=self.custom_memory,
                supervisor_output=supervisor_output,
                available_subject=self.available_subject
            )
            bot_response = result or "Sorry, I'm facing some issues while processing your request. Please try again later."   
            return bot_response

        elif route == "out_of_scope":
            bot_response = supervisor_output.response
            self.custom_memory.conversation.append(
                TurnTeacher(
                    sender="bot", 
                    message=bot_response, 
                    timestamp=datetime.now(),
                    route=route,
                    reason=reason
                )
            )
            return bot_response

        fallback = "Sorry, I'm facing some issues while processing your request. Please try again later."
        self.custom_memory.conversation.append(
            TurnTeacher(
                sender="bot", 
                message=fallback, 
                timestamp=datetime.now(),
                route=route,
                reason=reason
            )
        )
        return fallback


async def kickoff(
    instructor_id: str,
    instructor_email: str,
    user_query: str,
    session_token: str,
    available_subjects: List[str]
):
    try:
        # 1) Fetch existing memory from Redis
        raw = await redis_client.get(f"session:{session_token}")
        custom_memory = CustomMemoryTeacher.model_validate_json(raw)

        # 2) Instantiate flow with existing memory
        flow = InstructorAgentFlow(
            instructor_id=instructor_id,
            instructor_email=instructor_email,
            user_query=user_query,
            custom_memory=custom_memory,  # pass in loaded memory
            available_subject=available_subjects
        )

        # 3) Execute the flow
        result = await flow.kickoff_async()

        # 4) Persist updated memory back to Redis
        updated_json = flow.custom_memory.model_dump_json()
        await redis_client.update(
            f"session:{session_token}",
            updated_json
        )

        return result
    except Exception as e:
        print(e)
        raise

def plot():
    student_agent_flow = InstructorAgentFlow()
    student_agent_flow.plot()
