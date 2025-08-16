from typing import List
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from crewai.agents.agent_builder.base_agent import BaseAgent
from crew_flows_student.utils import llm
from pydantic_models.crew_models import AnnouncementIntentOutput

@CrewBase
class AnnouncementIntentCrew:
    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def announcement_supervisor(self):
        return Agent(
            config=self.agents_config["announcement_supervisor"],
            llm=llm,
            verbose=True
        )

    @task
    def route_announcement_action_task(self):
        return Task(
            config=self.tasks_config["route_announcement_action_task"],
            output_pydantic=AnnouncementIntentOutput
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
