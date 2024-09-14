import os
from crewai import Agent
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
from langchain_groq import ChatGroq

# Initialize LLM and tools
llm = ChatGroq(api_key=os.environ['GROQ_API_KEY'], model='llama-3.1-70b-versatile')
google_search_tool = SerperDevTool(api_key=os.environ["SERPER_API_KEY"])

# Agents
news_researcher = Agent(
    role="News Researcher",
    goal="Summarize the information from the top three news articles for a given topic.",
    backstory=(
        "With years of experience in journalism, you have a keen eye for identifying newsworthy stories. "
        "Your expertise lies in quickly gathering and summarizing the most relevant and recent information from various sources. "
        "Your dedication to providing accurate and up-to-date news has earned you a reputation as a reliable and thorough researcher."
    ),
    llm=llm,
    tools=[google_search_tool, ScrapeWebsiteTool()],
    allow_delegation=False,
    verbose=False
)

senior_script_writer = Agent(
    role="Senior Script Writer",
    goal="Write a podcast script based on the provided news summary in the required format and within the specified constraints",
    backstory=(
        "You are an experienced scriptwriter with a talent for creating engaging and informative content. "
        "You simplify complex topics and present them in an entertaining and easily digestible manner. "
        "You will write the script in the specified JSON format and within the specified constraints"
    ),
    llm=llm,
    allow_delegation=False,
    verbose=False
)
