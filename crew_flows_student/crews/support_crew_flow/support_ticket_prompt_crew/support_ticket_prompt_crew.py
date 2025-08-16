from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from crew_flows_student.utils import llm

@CrewBase
class SupportTicketPromptCrew:
    agents_config = "config/agents.yaml"
    tasks_config  = "config/tasks.yaml"

    @agent
    def support_ticket_prompt_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["support_ticket_prompt_agent"],
            llm=llm,
            verbose=True
        )

    @task
    def support_ticket_prompt_task(self) -> Task:
        return Task(config=self.tasks_config["support_ticket_prompt_task"])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[self.support_ticket_prompt_agent()],
            tasks=[self.support_ticket_prompt_task()],
            process=Process.sequential,
            verbose=True
        )
