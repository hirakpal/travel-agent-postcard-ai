import json
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
    You are an expert Travel Concierge. Return ONLY a JSON object:
    {
      "combinations": [{
        "name": "Luxury Relaxed",
        "days": [{
          "day": 1, 
          "plan": "Visit Eiffel Tower", 
          "insight": "Witness the city skyline from the summit; best viewed at sunset.", 
          "transport": "Metro line 6", 
          "lat": 48.8584, "lon": 2.2945
        }],
        "travel_logistics": {"suggestion": "Fly into CDG, take RER B train.", "estimated_cost": 5000}
      }]
    }
    1. Generate 4 plans. 
    2. Add an 'insight' field for each place that captures what they will see and why it's worth it.
    """)
    # ... (rest of parsing logic) ...
    return {"itinerary": parsed_data}
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
