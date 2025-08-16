from typing import List
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from crewai.agents.agent_builder.base_agent import BaseAgent
from crew_flows_student.utils import fetch_tools, llm
from crewai.tasks.conditional_task import ConditionalTask
from crew_flows_teacher.utils import check_student_id
from pydantic_models.crew_models import EvaluationFeedbackResponse2, StudentID

@CrewBase
class EvaluationFeedbackCrew:
    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def evaluation_student_id_fetcher(self) -> Agent:
        return Agent(
            config=self.agents_config["evaluation_student_id_fetcher"],
            llm=llm,
            verbose=True
        )

    @agent
    def evaluation_feedback_fetcher(self) -> Agent:
        return Agent(
            config=self.agents_config["evaluation_feedback_fetcher"],
            llm=llm,
            verbose=True,
            tools=[
                fetch_tools("get_evaluation_feedback")
            ]
        )

    @task
    def extract_student_id_task(self) -> Task:
        return Task(
            config=self.tasks_config["extract_student_id_task"],
            output_pydantic=StudentID
        )

    @task
    def extract_suggested_evaluation_feedback_task(self) -> ConditionalTask:
        return ConditionalTask(
            condition=check_student_id,
            config=self.tasks_config["extract_suggested_evaluation_feedback_task"],
            context=[self.extract_student_id_task()],
            output_pydantic=EvaluationFeedbackResponse2
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
