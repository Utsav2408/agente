from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from crew_flows_student.utils import llm
from crew_flows_teacher.utils import fetch_tools
from pydantic_models.crew_models import CreateAnnouncementResponse

@CrewBase
class ApproveSuggestionCrew:
    agents_config = "config/agents.yaml"
    tasks_config  = "config/tasks.yaml"

    @agent
    def announcement_approve(self) -> Agent:
        return Agent(
            config=self.agents_config["announcement_approve"],
            llm=llm,
            verbose=True,
            tools=[
                fetch_tools("create_announcement")
            ]
        )

    @task
    def create_announcement_task(self) -> Task:
        return Task(
            config=self.tasks_config["create_announcement_task"],
            output_pydantic=CreateAnnouncementResponse
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
