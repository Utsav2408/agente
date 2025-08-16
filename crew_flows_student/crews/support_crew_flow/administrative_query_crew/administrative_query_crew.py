from typing import List
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from crewai.agents.agent_builder.base_agent import BaseAgent
from crew_flows_student.utils import fetch_tools, llm
from pydantic_models.crew_models import AdministrativeModelOutput, AdministrativeQueryRewritter, FinalResponseModel

@CrewBase
class AdministrativeQueryCrew:
    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def query_rewritter(self) -> Agent:
        return Agent(
            config=self.agents_config["query_rewritter"],
            llm=llm,
            verbose=True
        )

    @agent
    def retriever_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["retriever_agent"],
            llm=llm,
            verbose=True,
            tools=[
                fetch_tools("fetch_answer_administrative_tool"),
            ]
        )

    @agent
    def answer_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["answer_agent"],
            llm=llm,
            verbose=True
        )

    @task
    def query_rewritter_task(self) -> Task:
        return Task(
            config=self.tasks_config["query_rewritter_task"],
            output_pydantic=AdministrativeQueryRewritter
        )

    @task
    def retriever_agent_task(self) -> Task:
        return Task(
            config=self.tasks_config["retriever_agent_task"],
            context=[self.query_rewritter_task()],
            output_pydantic=AdministrativeModelOutput
        )

    @task
    def answer_user_query_task(self) -> Task:
        return Task(
            config=self.tasks_config["answer_user_query_task"],
            context=[self.retriever_agent_task()],
            output_pydantic=FinalResponseModel
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
