from typing import List
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, crew, task
from crew_flows_student.utils import fetch_tools, llm
from crewai.tasks.conditional_task import ConditionalTask
from crewai.agents.agent_builder.base_agent import BaseAgent
from crew_flows_teacher.utils import check_answer_key_parameters
from pydantic_models.crew_models import AnswerKeyDetailParams, AnswerKeyDetailResponse


@CrewBase
class AnswerKeyDetailCrew:
    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config  = "config/tasks.yaml"

    @agent
    def answer_key_detail_data_fetcher(self) -> Agent:
        return Agent(
            config=self.agents_config["answer_key_detail_data_fetcher"],
            llm=llm,
            verbose=True
        )

    @agent
    def answer_key_detail_fetcher(self) -> Agent:
        return Agent(
            config=self.agents_config["answer_key_detail_fetcher"],
            llm=llm,
            verbose=True,
            tools=[
                fetch_tools("fetch_answer_keys")
            ]
        )

    @agent
    def answer_key_detail_beautifier(self) -> Agent:
        return Agent(
            config=self.agents_config["answer_key_detail_beautifier"],
            llm=llm,
            verbose=True
        )

    @task
    def extract_data_task(self) -> Task:
        return Task(
            config=self.tasks_config["extract_data_task"],
            output_pydantic=AnswerKeyDetailParams
        )

    @task
    def fetch_answer_key_task(self) -> ConditionalTask:
        return ConditionalTask(
            condition=check_answer_key_parameters,
            config=self.tasks_config["fetch_answer_key_task"],
            context=[self.extract_data_task()],
            output_pydantic=AnswerKeyDetailResponse
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
