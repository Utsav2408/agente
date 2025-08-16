from typing import List
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from crewai.agents.agent_builder.base_agent import BaseAgent
from crew_flows_student.utils import llm
from pydantic_models.crew_models import RoutingOutput

@CrewBase
class SupervisorCrew:

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def supervisor(self) -> Agent:
        return Agent(
            config=self.agents_config["supervisor"],
            llm=llm,
            verbose=True
        )

    @task
    def handle_user_query_task(self) -> Task:
        return Task(
            config=self.tasks_config["handle_user_query_task"],
            output_pydantic=RoutingOutput
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
