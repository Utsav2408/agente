from typing import List
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, crew, task
from crew_flows_student.utils import fetch_tools, llm
from crewai.agents.agent_builder.base_agent import BaseAgent
from pydantic_models.crew_models import SupportTicketData, SupportTicketDataFetcherResponse


@CrewBase
class SupportTicketDetailCrew:
    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config  = "config/tasks.yaml"

    @agent
    def support_ticket_detail_data_fetcher(self) -> Agent:
        return Agent(
            config=self.agents_config["support_ticket_detail_data_fetcher"],
            llm=llm,
            verbose=True,
            tools=[
                fetch_tools("get_support_ticket_by_id_request_assignee"),
                fetch_tools("get_all_support_ticket_by_assignee"),
            ]
        )

    @agent
    def support_ticket_detail_beautifier(self) -> Agent:
        return Agent(
            config=self.agents_config["support_ticket_detail_beautifier"],
            llm=llm,
            verbose=True
        )

    @task
    def fetch_support_ticket_task(self) -> Task:
        return Task(
            config=self.tasks_config["fetch_support_ticket_task"],
            output_pydantic=SupportTicketData
        )

    @task
    def beautify_support_ticket_response_task(self) -> Task:
        return Task(
            config=self.tasks_config["beautify_support_ticket_response_task"],
            context=[self.fetch_support_ticket_task()],
            output_pydantic=SupportTicketDataFetcherResponse
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
