import os
import time
from typing import TypedDict, List
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

# --- Schemas ---
class Location(BaseModel):
    name: str
    lat: float
    lon: float

class Itinerary(BaseModel):
    destination: str
    nodes: List[Location]
    is_confirmed: bool = False

class AgentState(TypedDict):
    itinerary: dict
    last_check_timestamp: float
    last_update_seq: int
    feedback: List[str]

# --- LLM Logic ---
llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

def plan_itinerary(destination: str, feedback_history: List[str] = None):
    context = f"User Preferences: {'; '.join(feedback_history)}" if feedback_history else ""
    prompt = f"Create a 2-day travel plan for {destination}. {context}. Return names, latitude, and longitude."
    structured_llm = llm.with_structured_output(Itinerary)
    return structured_llm.invoke(prompt)

# --- Nodes ---
def planning_node(state: AgentState):
    current_seq = state.get('last_update_seq', 0)
    itinerary_obj = plan_itinerary(state['itinerary']['destination'], state.get('feedback'))
    return {
        "itinerary": itinerary_obj.model_dump(),
        "last_update_seq": current_seq + 1
    }

def reprice_node(state: AgentState):
    return {"last_check_timestamp": time.time()}

def booking_node(state: AgentState):
    itinerary = state['itinerary']
    itinerary['is_confirmed'] = True
    return {"itinerary": itinerary}

def feedback_node(state: AgentState):
    return {"feedback": state.get('feedback', []) + ["User preference updated"]}

# --- Graph Definition ---
def is_price_stale(last_check_timestamp: float):
    return (time.time() - last_check_timestamp) > 180

def decide_route(state):
    return "reprice" if is_price_stale(state['last_check_timestamp']) else "book"

builder = StateGraph(AgentState)
builder.add_node("planner", planning_node)
builder.add_node("reprice_node", reprice_node)
builder.add_node("booking_node", booking_node)
builder.add_node("feedback_agent", feedback_node)
builder.set_entry_point("planner")
builder.add_conditional_edges("planner", decide_route, {"reprice": "reprice_node", "book": "booking_node"})
builder.add_edge("reprice_node", "booking_node")
builder.add_edge("booking_node", "feedback_agent")
builder.add_edge("feedback_agent", END)

app = builder.compile()
