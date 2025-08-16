from typing import List
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.tasks.conditional_task import ConditionalTask
from crew_flows_student.utils import check_all_params, check_if_tool_call, fetch_tools, llm
from pydantic_models.crew_models import FinalResponseModel, GatherPerformanceReport, IdentifyParametersResponse, ResponseModel

@CrewBase
class PerformanceCrew:
    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def student_performance_guider(self) -> Agent:
        return Agent(
            config=self.agents_config["student_performance_guider"],
            llm=llm,
            verbose=True,
            tools=[
                fetch_tools("fetch_exam_scorecard"),
                fetch_tools("fetch_all_exam_scorecards"),
                fetch_tools("resolve_date_tool")
            ]
        )

    @agent
    def student_answer_builder(self) -> Agent:
        return Agent(
            config=self.agents_config["student_answer_builder"],
            llm=llm,
            verbose=True
        )

    @task
    def identify_all_variables(self) -> Task:
        return Task(
            config=self.tasks_config["identify_all_variables"],
            output_pydantic=IdentifyParametersResponse
        )

    @task
    def construct_follow_up_question(self) -> Task:
        return Task(
            config=self.tasks_config["construct_follow_up_question"],
            output_pydantic=ResponseModel
        )

    @task
    def fetch_performance_reports(self) -> ConditionalTask:
        return ConditionalTask(
            condition=check_all_params,
            config=self.tasks_config["fetch_performance_reports"],
            output_pydantic=GatherPerformanceReport
        )

    @task
    def construct_answer(self) -> ConditionalTask:
        return ConditionalTask(
            condition=check_if_tool_call,
            config=self.tasks_config["construct_answer"],
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
