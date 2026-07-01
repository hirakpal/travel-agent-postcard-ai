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
    1. Analyze the user's budget and travel mode.
    2. Generate 4 distinct day-wise itinerary combinations (e.g., 'Luxury Relaxed', 'Budget Adventure', 'Cultural Deep-Dive', 'Family Friendly').
    3. Include for each combination: 
       - Day-wise plan with directions.
       - Optimized transport options between nodes.
       - If Flight/Bus, suggest time-matched options.
       - If Driving, account for arrival/departure times.
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
