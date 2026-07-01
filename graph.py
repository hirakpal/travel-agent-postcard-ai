import json
import time
from typing import TypedDict, List, Annotated
import operator
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

class AgentState(TypedDict):
    itinerary: dict
    logistics: dict
    feedback: Annotated[List[str], operator.add]

llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

def planning_node(state: AgentState):
    system_prompt = SystemMessage(content="""
    You are an expert AI Travel Concierge.
    Return ONLY a JSON object:
    {
      "combinations": [
        {
          "name": "Luxury Relaxed",
          "days": [{"day": 1, "plan": "...", "transport": "...", "directions": "..."}],
          "travel_logistics": {"suggestion": "...", "estimated_cost": 0}
        }
      ]
    }
    Generate 4 distinct itinerary combinations based on the user's budget and travel mode.
    """)
    messages = [system_prompt, HumanMessage(content=f"Plan trip to: {state['itinerary'].get('destination')} with logistics: {state.get('logistics')}")]
    
    response = llm.invoke(messages)
    try:
        parsed_data = json.loads(response.content.replace("```json", "").replace("```", "").strip())
    except:
        parsed_data = {"combinations": []}
    return {"itinerary": parsed_data}

builder = StateGraph(AgentState)
builder.add_node("planner", planning_node)
builder.set_entry_point("planner")
builder.add_edge("planner", END)
app = builder.compile()
