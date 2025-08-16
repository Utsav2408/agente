from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from crew_flows_student.utils import llm
from pydantic_models.crew_models import EvaluateStudentResponse

@CrewBase
class EvaluateStudentAnswerCrew:
    agents_config = "config/agents.yaml"
    tasks_config  = "config/tasks.yaml"

    @agent
    def evaluate_student_answer_handler(self) -> Agent:
        return Agent(
            config=self.agents_config["evaluate_student_answer_handler"],
            llm=llm,
            verbose=True
        )

    @task
    def evaluate_student_answer_task(self) -> Task:
        return Task(
            config=self.tasks_config["evaluate_student_answer_task"],
            output_pydantic=EvaluateStudentResponse
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
