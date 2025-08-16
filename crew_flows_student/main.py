from datetime import datetime
from typing import List
from crewai.flow import Flow, listen, start
from crew_flows_student.crews.performance_crew.performance_crew import PerformanceCrew
from crew_flows_student.crews.subjective_crew.subjective_crew import SubjectiveCrew
from crew_flows_student.crews.supervisor_crew.supervisor import SupervisorCrew, RoutingOutput
from crew_flows_student.crews.support_crew_flow import support_crew_flow
from pydantic_models.login_model import CustomMemory, Turn
from redis_db.redis_client import redis_client
from logger.python_log import global_logger

import mlflow

mlflow.crewai.autolog()

class StudentAgentFlow(Flow):
    def __init__(
        self,
        student_id: str,
        grade: str,
        user_query: str,
        subject_list: List[str],
        custom_memory: CustomMemory
    ):
        super().__init__()
        self.student_id = student_id
        self.grade = grade
        self.user_query = user_query
        self.subject_list = subject_list
        self.custom_memory = custom_memory

    @start()
    async def supervisor(self):
        # Prepare payload
        sup_payload = {
            "user_input": self.user_query,
            "available_subjects": ', '.join(self.subject_list),
            "conversation_history": self.custom_memory.model_dump_json(),
            "last_reason": self.custom_memory.last_reason,
            "last_route": self.custom_memory.last_route,
            "last_subject": self.custom_memory.last_subject,
        }
        global_logger.info("Supervisor payload: %s", sup_payload)

        # Call supervisor crew with error handling
        try:
            raw_res = SupervisorCrew().crew().kickoff(sup_payload)
            pyd_res: RoutingOutput = raw_res.pydantic
        except Exception as e:
            global_logger.error("SupervisorCrew kickoff error", exc_info=True)
            # default fallback routing
            pyd_res = RoutingOutput(route="support", reason="escalation")

        # update memory
        self.custom_memory.last_route = pyd_res.route
        self.custom_memory.last_reason = pyd_res.reason
        return pyd_res

    @listen(supervisor)
    async def call_crew(self, supervisor_output: RoutingOutput):
        route = supervisor_output.route
        reason = supervisor_output.reason
        global_logger.info("Handling route '%s' with reason '%s'", route, reason)

        # Record the user message
        self.custom_memory.conversation.append(Turn(sender="user", message=self.user_query, timestamp=datetime.now()))

        # Helper for error-handled kickoff
        def safe_kickoff(crew_cls, payload, pydantic=False):
            global_logger.info("Payload for %s: %s", crew_cls.__name__, payload)
            try:
                res = crew_cls().crew().kickoff(payload)
                return res.pydantic if pydantic else res.raw
            except Exception as e:
                global_logger.error("Error in %s", crew_cls.__name__, exc_info=True)
                return None

        # 1) New Support Flow
        if route == "support":
            result = await support_crew_flow.kickoff(
                student_id=self.student_id,
                user_query=self.user_query,
                custom_memory=self.custom_memory
            )
            bot_response = result or "Sorry, I'm facing some issues while processing your request. Please try again later."
            self.custom_memory.conversation.append(Turn(sender="bot", message=bot_response, timestamp=datetime.now()))
            return bot_response

        # 2) Course-related queries
        if route == "course":
            payload = {
                "user_input": self.user_query,
                "available_subjects": ', '.join(self.subject_list),
                "conversation_history": self.custom_memory.model_dump_json(),
                "last_subject": self.custom_memory.last_subject,
                "supervisor_output": supervisor_output.model_dump_json(),
                "grade": self.grade,
            }
            out = safe_kickoff(SubjectiveCrew, payload, pydantic=True)
            if out:
                answer = out.response
                formatted_sources = "\n".join(f"- {src}" for src in out.source)
                answer += f"\n\nSources:\n{formatted_sources}"
                self.custom_memory.conversation.append(Turn(sender="bot", message=answer, timestamp=datetime.now()))
                self.custom_memory.last_subject = out.last_subject
                return answer
            else:
                fallback = "Sorry, I couldn't process your course question right now."
                self.custom_memory.conversation.append(Turn(sender="bot", message=fallback, timestamp=datetime.now()))
                return fallback

        # 3) Performance-related queries
        if route == "performance":
            payload = {
                "student_query": self.user_query,
                "allowed_courses": ', '.join(self.subject_list),
                "conversation_history": self.custom_memory.model_dump_json(),
                "grade": self.grade,
                "student_id": self.student_id,
            }
            result = safe_kickoff(PerformanceCrew, payload, pydantic=True)
            bot_response = result.response or "Sorry, I couldn't retrieve your performance details right now."
            self.custom_memory.conversation.append(Turn(sender="bot", message=bot_response, timestamp=datetime.now()))
            return bot_response

        if route == "out_of_scope":
            bot_response = supervisor_output.response
            self.custom_memory.conversation.append(Turn(sender="bot", message=bot_response, timestamp=datetime.now()))
            return bot_response            
        # 4) Fallback
        fallback = "I'm still learning. Could you rephrase?"
        self.custom_memory.conversation.append(Turn(sender="bot", message=fallback, timestamp=datetime.now()))
        return fallback


async def kickoff(
    student_id: str,
    grade: str,
    user_query: str,
    subject_list: List[str],
    session_token: str
):
    try:
        # 1) Fetch existing memory from Redis
        raw = await redis_client.get(f"session:{session_token}")
        custom_memory = CustomMemory.model_validate_json(raw)

        # 2) Instantiate flow with existing memory
        flow = StudentAgentFlow(
            student_id=student_id,
            grade=grade,
            user_query=user_query,
            subject_list=subject_list,
            custom_memory=custom_memory  # pass in loaded memory
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
    student_agent_flow = StudentAgentFlow()
    student_agent_flow.plot()
