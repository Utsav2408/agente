from typing import List
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from crewai.agents.agent_builder.base_agent import BaseAgent
from crew_flows_student.utils import fetch_tools, llm
from crewai.tasks.conditional_task import ConditionalTask
from crew_flows_teacher.utils import check_announcement_parameters
from pydantic_models.crew_models import AnnouncementDraftResponse, AnnouncementFindParametersResponse

@CrewBase
class AnnouncementCreatorCrew:
    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def announcement_creator_data_fetcher(self) -> Agent:
        return Agent(
            config=self.agents_config["announcement_creator_data_fetcher"],
            llm=llm,
            verbose=True,
            tools=[
                fetch_tools("resolve_date_tool")
            ]
        )

    @agent
    def announcement_creator_draft_fetcher(self) -> Agent:
        return Agent(
            config=self.agents_config["announcement_creator_draft_fetcher"],
            llm=llm,
            verbose=True
        )

    @task
    def extract_data_task(self) -> Task:
        return Task(
            config=self.tasks_config["extract_data_task"],
            output_pydantic=AnnouncementFindParametersResponse
        )

    @task
    def formulate_draft_announcement_task(self) -> ConditionalTask:
        return ConditionalTask(
            condition=check_announcement_parameters,
            config=self.tasks_config["formulate_draft_announcement_task"],
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
