from typing import List
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from crewai.agents.agent_builder.base_agent import BaseAgent
from crew_flows_teacher.utils import fetch_tools, llm
from pydantic_models.crew_models import ClassifiedSubject, FinalResponseModel, RetrievedContentWithoutSource


@CrewBase
class ResolveCourseQuery:
    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def subject_classifier(self) -> Agent:
        return Agent(
            config=self.agents_config["subject_classifier"],
            llm=llm,
            verbose=True
        )

    @agent
    def retriever(self) -> Agent:
        return Agent(
            config=self.agents_config["retriever"],
            llm=llm,
            tools=[fetch_tools("retrieve_context")],
            verbose=True
        )

    @agent
    def answer_generator(self) -> Agent:
        return Agent(
            config=self.agents_config["answer_generator"],
            llm=llm,
            verbose=True
        )

    @task
    def classify_subject_task(self) -> Task:
        return Task(
            config=self.tasks_config["classify_subject_task"],
            output_pydantic=ClassifiedSubject
        )

    @task
    def retrieve_info_task(self) -> Task:
        return Task(
            config=self.tasks_config["retrieve_info_task"],
            context=[self.classify_subject_task()],
            output_pydantic=RetrievedContentWithoutSource
        )

    @task
    def generate_final_answer_task(self) -> Task:
        return Task(
            config=self.tasks_config["generate_final_answer_task"],
            context=[self.retrieve_info_task()],
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
