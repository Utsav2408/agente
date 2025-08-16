import json, os
from crewai import LLM, TaskOutput
from crewai_tools import MCPServerAdapter
from dotenv import load_dotenv

load_dotenv()

adapter = MCPServerAdapter(
    {
        "url":"http://127.0.0.1:8000/mcp"
    }
)

llm = LLM(
    model="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY")
)

def fetch_tools(name: str):
    tools = adapter.tools
    return next((t for t in tools if t.name == name), None)

# performance crew utils

def check_all_params(output: TaskOutput):
    try:
        return json.loads(output.raw)["has_all_fields"]
    except Exception as e:
        print(e)
        return False

def check_if_tool_call(output: TaskOutput):
    try:
        return json.loads(output.raw)["done_tool_call"]
    except Exception as e:
        print(e)
        return False
    
# fetch ticket crew utils

def isTicketPresent(output: TaskOutput) -> bool:
    try:
        return json.loads(output.raw)["has_ticket_id"]
    except Exception as e:
        print(e)
        return False

def isTicketNotPresent(output: TaskOutput) -> bool:
    try:
        return not json.loads(output.raw)["has_ticket_id"]
    except Exception as e:
        print(e)
        return False
    
# raise ticket crew utils

def isFollowUpNotNeeded(output: TaskOutput) -> bool:
    try:
        return not json.loads(output.raw)["follow_up_needed"]
    except Exception as e:
        print(e)
        return True