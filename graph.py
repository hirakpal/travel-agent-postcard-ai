import json
import time
from typing import TypedDict, List, Annotated
import operator
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

class AgentState(TypedDict):
    itinerary: dict
    travel_date: str
    feedback: Annotated[List[str], operator.add]

llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

def planning_node(state: AgentState):
    system_prompt = SystemMessage(content="""
    You are an expert AI Travel Concierge.
    Return ONLY a JSON object with this exact structure:
    {
      "combinations": [
        {
          "name": "Luxury Relaxed",
          "days": [
            {"day": 1, "plan": "...", "transport": "...", "directions": "..."},
            ...
          ],
          "travel_logistics": {"suggestion": "...", "estimated_cost": 0}
        }
      ]
    }
    1. Generate 4 distinct combinations (e.g., Luxury, Budget, Adventure, Cultural).
    2. Incorporate budget and travel mode constraints provided by the user.
    3. If driving, align plans with arrival/departure times. 
    4. If flight/bus, suggest specific time-matched transit options.
    No conversational filler. Only valid JSON.
""")
    messages = [
        system_prompt, 
        HumanMessage(content=f"Plan trip to: {state['itinerary']['destination']} on {state.get('travel_date')}. Feedback: {state.get('feedback', [''])[0]}")
    ]
    
    response = llm.invoke(messages)
    try:
        parsed_data = json.loads(response.content.replace("```json", "").replace("```", "").strip())
    except:
        parsed_data = {"destination": state['itinerary']['destination'], "nodes": []}
    return {"itinerary": parsed_data}

builder = StateGraph(AgentState)
builder.add_node("planner", planning_node)
builder.set_entry_point("planner")
builder.add_edge("planner", END)
app = builder.compile()
