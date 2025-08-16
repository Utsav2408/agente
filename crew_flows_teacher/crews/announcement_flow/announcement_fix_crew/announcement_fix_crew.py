from typing import List
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from crewai.agents.agent_builder.base_agent import BaseAgent
from crew_flows_student.utils import llm
from crew_flows_teacher.utils import fetch_tools
from pydantic_models.crew_models import AnnouncementDraftResponse

@CrewBase
class AnnouncementFixCrew:
    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def announcement_fix(self) -> Agent:
        return Agent(
            config=self.agents_config["announcement_fix"],
            llm=llm,
            verbose=True,
            tools=[
                fetch_tools("resolve_date_tool")
            ]
        )

    @task
    def fix_announcement_task(self) -> Task:
        return Task(
            config=self.tasks_config["fix_announcement_task"],
            output_pydantic=AnnouncementDraftResponse
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
