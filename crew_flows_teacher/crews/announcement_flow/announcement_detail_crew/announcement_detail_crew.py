from typing import List
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, crew, task
from crew_flows_student.utils import fetch_tools, llm
from crewai.agents.agent_builder.base_agent import BaseAgent

from pydantic_models.crew_models import AnnouncementCrewData, AnnouncementCrewResponseData


@CrewBase
class AnnouncementDetailCrew:
    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config  = "config/tasks.yaml"

    @agent
    def announcement_detail_data_fetcher(self) -> Agent:
        return Agent(
            config=self.agents_config["announcement_detail_data_fetcher"],
            llm=llm,
            verbose=True,
            tools=[
                fetch_tools("fetch_announcement_by_id"),
                fetch_tools("fetch_all_announcements_for_instructor"),
            ]
        )

    @agent
    def announcement_detail_beautifier(self) -> Agent:
        return Agent(
            config=self.agents_config["announcement_detail_beautifier"],
            llm=llm,
            verbose=True
        )

    @task
    def fetch_announcement_task(self) -> Task:
        return Task(
            config=self.tasks_config["fetch_announcement_task"],
            output_pydantic=AnnouncementCrewData
        )

    @task
    def beautify_announcement_response_task(self) -> Task:
        return Task(
            config=self.tasks_config["beautify_announcement_response_task"],
            context=[self.fetch_announcement_task()],
            output_pydantic=AnnouncementCrewResponseData
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
