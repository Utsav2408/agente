from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from crew_flows_student.utils import llm
from crew_flows_teacher.utils import fetch_tools
from pydantic_models.crew_models import ApproveSuggestionModel

@CrewBase
class ApproveSuggestionCrew:
    agents_config = "config/agents.yaml"
    tasks_config  = "config/tasks.yaml"

    @agent
    def approve_suggestion_handler(self) -> Agent:
        return Agent(
            config=self.agents_config["approve_suggestion_handler"],
            llm=llm,
            verbose=True,
            tools=[
                fetch_tools("resolve_support_ticket_tool")
            ]
        )

    @task
    def approve_suggestion_and_resolve_ticket_task(self) -> Task:
        return Task(
            config=self.tasks_config["approve_suggestion_and_resolve_ticket_task"],
            output_pydantic=ApproveSuggestionModel
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
