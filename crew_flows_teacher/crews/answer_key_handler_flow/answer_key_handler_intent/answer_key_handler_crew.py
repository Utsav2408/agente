from typing import List
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from crewai.agents.agent_builder.base_agent import BaseAgent
from crew_flows_student.utils import llm
from pydantic_models.crew_models import AnswerKeyIntentOutput

@CrewBase
class AnswerKeyIntentCrew:
    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def handle_answer_key_supervisor(self):
        return Agent(
            config=self.agents_config["handle_answer_key_supervisor"],
            llm=llm,
            verbose=True
        )

    @task
    def route_answer_key_task(self):
        return Task(
            config=self.tasks_config["route_answer_key_task"],
            output_pydantic=AnswerKeyIntentOutput
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
