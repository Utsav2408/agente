from typing import List
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from crewai.agents.agent_builder.base_agent import BaseAgent
from crew_flows_student.utils import fetch_tools, llm
from crewai.tasks.conditional_task import ConditionalTask
from crew_flows_teacher.utils import check_support_ticket_id
from pydantic_models.crew_models import SuggestedToolCall, SuggestedToolCallResponse, SupportTicketID

@CrewBase
class ResolveTicketCrew:
    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def resolve_ticket_support_id_fetcher(self) -> Agent:
        return Agent(
            config=self.agents_config["resolve_ticket_support_id_fetcher"],
            llm=llm,
            verbose=True
        )

    @agent
    def resolve_ticket_data_fetcher(self) -> Agent:
        return Agent(
            config=self.agents_config["resolve_ticket_data_fetcher"],
            llm=llm,
            verbose=True,
            tools=[
                fetch_tools("get_support_ticket_suggestion_request_assignee")
            ]
        )

    @agent
    def resolve_ticket_beautifier(self) -> Agent:
        return Agent(
            config=self.agents_config["resolve_ticket_beautifier"],
            llm=llm,
            verbose=True
        )

    @task
    def extract_support_id_task(self) -> Task:
        return Task(
            config=self.tasks_config["extract_support_id_task"],
            output_pydantic=SupportTicketID
        )

    @task
    def extract_suggested_reply_task(self) -> ConditionalTask:
        return ConditionalTask(
            condition=check_support_ticket_id,
            config=self.tasks_config["extract_suggested_reply_task"],
            output_pydantic=SuggestedToolCall
        )

    @task
    def beautify_suggested_reply_task(self) -> ConditionalTask:
        return ConditionalTask(
            condition=check_support_ticket_id,
            config=self.tasks_config["beautify_suggested_reply_task"],
            output_pydantic=SuggestedToolCallResponse
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
