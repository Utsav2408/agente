from typing import List
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from crewai.agents.agent_builder.base_agent import BaseAgent
from crew_flows_student.utils import llm
from pydantic_models.crew_models import FetchQuestionNumber

@CrewBase
class FetchQuestionNumberCrew:
    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def fetch_question_id(self) -> Agent:
        return Agent(
            config=self.agents_config["fetch_question_id"],
            llm=llm,
            verbose=True
        )

    @task
    def extract_question_id_task(self) -> Task:
        return Task(
            config=self.tasks_config["extract_question_id_task"],
            output_pydantic=FetchQuestionNumber
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
