from typing import List
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, crew, task
from crew_flows_student.utils import fetch_tools, llm
from crewai.tasks.conditional_task import ConditionalTask
from crewai.agents.agent_builder.base_agent import BaseAgent
from crew_flows_teacher.utils import check_evaluation_parameters, check_evaluation_response
from pydantic_models.crew_models import EvaluationData, EvaluationDetailParams, EvaluationToolResponse


@CrewBase
class EvaluationHandlerDetailCrew:
    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config  = "config/tasks.yaml"

    @agent
    def evaluation_detail_data_fetcher(self) -> Agent:
        return Agent(
            config=self.agents_config["evaluation_detail_data_fetcher"],
            llm=llm,
            verbose=True
        )

    @agent
    def evaluation_detail_fetcher(self) -> Agent:
        return Agent(
            config=self.agents_config["evaluation_detail_fetcher"],
            llm=llm,
            verbose=True,
            tools=[
                fetch_tools("evaluation_details")
            ]
        )

    @agent
    def evaluation_detail_beautifier(self) -> Agent:
        return Agent(
            config=self.agents_config["evaluation_detail_beautifier"],
            llm=llm,
            verbose=True
        )

    @task
    def extract_data_task(self) -> Task:
        return Task(
            config=self.tasks_config["extract_data_task"],
            output_pydantic=EvaluationDetailParams
        )

    @task
    def fetch_evaluation_task(self) -> ConditionalTask:
        return ConditionalTask(
            condition=check_evaluation_parameters,
            config=self.tasks_config["fetch_evaluation_task"],
            context=[self.extract_data_task()],
            output_pydantic=EvaluationToolResponse
        )

    @task
    def beautify_evaluation_response_task(self) -> ConditionalTask:
        return ConditionalTask(
            condition=check_evaluation_response,
            config=self.tasks_config["beautify_evaluation_response_task"],
            context=[self.extract_data_task(), self.fetch_evaluation_task()],
            output_pydantic=EvaluationData
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
