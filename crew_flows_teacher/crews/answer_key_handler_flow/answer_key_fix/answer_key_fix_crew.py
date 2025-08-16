from typing import List
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from crewai.agents.agent_builder.base_agent import BaseAgent
from crew_flows_student.utils import llm
from pydantic_models.crew_models import AnswerKeyFixModel2

@CrewBase
class FixAnswerKeyCrew:
    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def fix_answer_key_handler(self) -> Agent:
        return Agent(
            config=self.agents_config["fix_answer_key_handler"],
            llm=llm,
            verbose=True
        )

    @task
    def fix_answer_key_task(self) -> Task:
        return Task(
            config=self.tasks_config["fix_answer_key_task"],
            output_pydantic=AnswerKeyFixModel2
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
