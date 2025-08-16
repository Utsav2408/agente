from typing import List
from crewai import Agent, Task, Crew, Process
from crewai.tasks.conditional_task import ConditionalTask
from crewai.project import CrewBase, agent, crew, task
from crew_flows_student.utils import fetch_tools, isTicketNotPresent, isTicketPresent, llm
from crewai.agents.agent_builder.base_agent import BaseAgent
from pydantic_models.crew_models import IdentifySupportTicketIdResponse


@CrewBase
class FetchTicketCrew:
    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config  = "config/tasks.yaml"

    @agent
    def fetch_support_ticket_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["fetch_support_ticket_agent"],
            llm=llm,
            verbose=True,
            tools=[
                fetch_tools("get_support_ticket_by_id"),
                fetch_tools("get_all_support_ticket_by_student_id"),
            ],
        )

    @agent
    def beautifier_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["beautifier_agent"],
            llm=llm,
            verbose=True,
        )

    @task
    def identify_support_ticket_id_task(self) -> Task:
        return Task(
            config=self.tasks_config["identify_support_ticket_id_task"],
            output_pydantic=IdentifySupportTicketIdResponse
        )

    @task
    def fetch_support_ticket_by_id_task(self) -> ConditionalTask:
        return ConditionalTask(
            condition=isTicketPresent,
            config=self.tasks_config["fetch_support_ticket_by_id_task"]
        )

    @task
    def list_support_tickets_by_student_task(self) -> ConditionalTask:
        return ConditionalTask(
            condition=isTicketNotPresent,
            config=self.tasks_config["list_support_tickets_by_student_task"]
        )

    @task
    def beautify_support_ticket_answer_task(self) -> Task:
        return Task(
            config=self.tasks_config["beautify_support_ticket_answer_task"]
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=[
                self.identify_support_ticket_id_task(),
                self.fetch_support_ticket_by_id_task(),
                self.identify_support_ticket_id_task(),
                self.list_support_tickets_by_student_task(),
                self.beautify_support_ticket_answer_task()
            ],
            process=Process.sequential,
            verbose=True,
            planning=True
        )
