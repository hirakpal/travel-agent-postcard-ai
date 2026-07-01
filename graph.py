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
    Return ONLY a valid JSON object. For each place, include:
    - name, lat, lng, category, avg_visit_duration
    - "weekday_hours": "09:00-18:00"
    - "weekend_hours": "10:00-20:00"
    - "is_open_on_date": boolean
    - "transport_options": "e.g., Metro line Blue, Bus 402"
    - "transport_tip": "e.g., Metro is fastest"
    Structure: {"destination": "Name", "nodes": [...]}
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
