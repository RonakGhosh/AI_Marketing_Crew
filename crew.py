from typing import List
from pydantic import BaseModel, Field
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import (
    SerperDevTool, ScrapeWebsiteTool,
    DirectoryReadTool, FileWriterTool, FileReadTool
)
import os

# Shared LLM w/ tight token budget for speed + cost
# LiteLLM-compatible kwargs are passed via "llm" below
llm = LLM(
    model="gemini/gemini-1.5-flash",
    temperature=0.3,
    top_p=0.8,
    # keep outputs tight; models may ignore hard caps, but helps
    max_tokens=900,
)

class Content(BaseModel):
    content_type: str = Field(..., description="blog, social post, email, reel")
    topic: str
    target_audience: str
    tags: List[str]
    content: str

def _optional_web_tools():
    """Attach web tools only when SERPER_API_KEY is present (saves time & cost)."""
    tools = [DirectoryReadTool('resources/drafts'), FileWriterTool(), FileReadTool()]
    if os.getenv("SERPER_API_KEY"):
        tools.insert(0, SerperDevTool())
        tools.insert(1, ScrapeWebsiteTool())
    return tools

@CrewBase
class TheMarketingCrew():
    """
    Lean marketing crew with compact outputs.
    """
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # --- Agents ---
    @agent
    def head_of_marketing(self) -> Agent:
        return Agent(
            config=self.agents_config['head_of_marketing'],
            tools=_optional_web_tools(),
            inject_date=True,
            llm=llm,
            allow_delegation=False,
            max_iter=2,     # keep small for speed
            max_rpm=3,
            verbose=False
        )

    @agent
    def content_creator_social_media(self) -> Agent:
        return Agent(
            config=self.agents_config['content_creator_social_media'],
            tools=_optional_web_tools(),
            inject_date=True,
            llm=llm,
            allow_delegation=False,
            max_iter=3,
            max_rpm=3,
            verbose=False
        )

    @agent
    def content_writer_blogs(self) -> Agent:
        # separate blog dir read to keep context tiny
        tools = [DirectoryReadTool('resources/drafts/blogs'), FileWriterTool(), FileReadTool()]
        if os.getenv("SERPER_API_KEY"):
            tools = [SerperDevTool(), ScrapeWebsiteTool()] + tools
        return Agent(
            config=self.agents_config['content_writer_blogs'],
            tools=tools,
            inject_date=True,
            llm=llm,
            allow_delegation=False,
            max_iter=3,
            max_rpm=3,
            verbose=False
        )

    @agent
    def seo_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config['seo_specialist'],
            tools=_optional_web_tools(),
            inject_date=True,
            llm=llm,
            allow_delegation=False,
            max_iter=2,
            max_rpm=3,
            verbose=False
        )

    # --- Tasks ---
    @task
    def market_research(self) -> Task:
        return Task(config=self.tasks_config['market_research'], agent=self.head_of_marketing())

    @task
    def prepare_marketing_strategy(self) -> Task:
        return Task(config=self.tasks_config['prepare_marketing_strategy'], agent=self.head_of_marketing())

    @task
    def create_content_calendar(self) -> Task:
        return Task(config=self.tasks_config['create_content_calendar'], agent=self.content_creator_social_media())

    @task
    def prepare_post_drafts(self) -> Task:
        return Task(config=self.tasks_config['prepare_post_drafts'], agent=self.content_creator_social_media(), output_json=Content)

    @task
    def prepare_scripts_for_reels(self) -> Task:
        return Task(config=self.tasks_config['prepare_scripts_for_reels'], agent=self.content_creator_social_media(), output_json=Content)

    @task
    def content_research_for_blogs(self) -> Task:
        return Task(config=self.tasks_config['content_research_for_blogs'], agent=self.content_writer_blogs())

    @task
    def draft_blogs(self) -> Task:
        return Task(config=self.tasks_config['draft_blogs'], agent=self.content_writer_blogs(), output_json=Content)

    @task
    def seo_optimization(self) -> Task:
        return Task(config=self.tasks_config['seo_optimization'], agent=self.seo_specialist(), output_json=Content)

    # --- Crew ---
    @crew
    def marketingcrew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=False,          # huge token saver
            planning=False,         # skip planner to save time/tokens
            max_rpm=3
            # planning_llm omitted to avoid extra calls
        )

if __name__ == "__main__":
    from datetime import datetime
    inputs = {
        "product_name": "AI Powered Excel Automation Tool",
        "target_audience": "Small and Medium Enterprises (SMEs)",
        "product_description": "Automates repetitive Excel tasks with AI.",
        "budget": "₹50,000",
        "current_date": datetime.now().strftime("%Y-%m-%d"),
    }
    crew = TheMarketingCrew()
    print(crew.marketingcrew().kickoff(inputs=inputs))
