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
from langchain_core.messages import SystemMessage, HumanMessage
# Assuming you are using ChatOpenAI or ChatGoogleGenerativeAI
# from langchain_openai import ChatOpenAI 

import json
from langchain_core.messages import SystemMessage, HumanMessage

def planning_node(state):
    system_prompt = SystemMessage(content="""
    You are the Postcard AI Travel Concierge. 
    Return ONLY a valid JSON object with the following structure:
    {
        "destination": "Name of destination",
        "nodes": [
            {"name": "Place", "lat": 0.0, "lng": 0.0, "avg_visit_duration": 60, "category": "Sight"},
            ...
        ]
    }
    No conversational text. Just the JSON.
    """)
    
    messages = [
        system_prompt, 
        HumanMessage(content=f"Plan a trip to: {state['itinerary']['destination']}. Preferences: {state['feedback'][0]}")
    ]
    
    # 1. Get the raw text response from the LLM
    response = llm.invoke(messages)
    raw_content = response.content # The actual text returned by LLM
    
    # 2. Clean and Parse the JSON
    try:
        # Remove markdown code blocks if the LLM included them
        clean_json = raw_content.replace("```json", "").replace("```", "").strip()
        parsed_data = json.loads(clean_json)
    except json.JSONDecodeError:
        # Fallback if the LLM fails to return valid JSON
        parsed_data = {"destination": state['itinerary']['destination'], "nodes": []}
    
    # 3. Return the correctly structured state update
    return {"itinerary": parsed_data}

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
