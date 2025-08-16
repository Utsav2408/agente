from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from crew_flows_student.utils import llm
from crew_flows_teacher.utils import fetch_tools
from pydantic_models.crew_models import AnswerKeySubmitModel

@CrewBase
class ApproveAnswerKeyCrew:
    agents_config = "config/agents.yaml"
    tasks_config  = "config/tasks.yaml"

    @agent
    def approve_answer_key_handler(self) -> Agent:
        return Agent(
            config=self.agents_config["approve_answer_key_handler"],
            llm=llm,
            verbose=True,
            tools=[
                fetch_tools("answer_key_submit")
            ]
        )

    @task
    def approve_answer_key_task(self) -> Task:
        return Task(
            config=self.tasks_config["approve_answer_key_task"],
            output_pydantic=AnswerKeySubmitModel
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
