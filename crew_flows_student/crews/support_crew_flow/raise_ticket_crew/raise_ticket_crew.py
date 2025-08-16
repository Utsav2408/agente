from typing import List
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from crewai.agents.agent_builder.base_agent import BaseAgent
from crew_flows_student.utils import fetch_tools, isFollowUpNotNeeded, llm
from pydantic_models.crew_models import FinalResponseModel, FollowUpForMoreInfo, RaiseTicketModel
from crewai.tasks.conditional_task import ConditionalTask

@CrewBase
class RaiseTicketCrew:
    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # @agent
    # def issue_validator_agent(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config["issue_validator_agent"],
    #         llm=llm,
    #         verbose=True
    #     )

    @agent
    def raise_support_ticket_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["raise_support_ticket_agent"],
            llm=llm,
            verbose=True,
            tools=[
                fetch_tools("raise_support_ticket_tool")
            ]
        )
    
    # @task
    # def issue_validator_task(self) -> Task:
    #     return Task(
    #         config=self.tasks_config["issue_validator_task"],
    #         output_pydantic=FollowUpForMoreInfo
    #     )

    # @task
    # def raise_support_ticket_task(self) -> ConditionalTask:
    #     return ConditionalTask(
    #         condition=isFollowUpNotNeeded,
    #         config=self.tasks_config["raise_support_ticket_task"],
    #         output_pydantic=FinalResponseModel
    #     )

    @task
    def raise_support_ticket_task(self) -> Task:
        return Task(
            config=self.tasks_config["raise_support_ticket_task"],
            output_pydantic=RaiseTicketModel
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
