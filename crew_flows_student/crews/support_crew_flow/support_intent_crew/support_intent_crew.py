from typing import List
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from crewai.agents.agent_builder.base_agent import BaseAgent
from crew_flows_student.utils import llm
from pydantic_models.crew_models import SupportIntentOutput

@CrewBase
class SupportIntentCrew:
    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def support_intent_agent(self):
        return Agent(
            config=self.agents_config["support_intent_agent"],
            llm=llm,
            verbose=True
        )

    @task
    def classify_support_intent_task(self):
        return Task(
            config=self.tasks_config["classify_support_intent_task"],
            output_pydantic=SupportIntentOutput
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
