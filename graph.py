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

def planning_node(state):
    # The expert persona
    system_prompt = SystemMessage(content="""
    You are the Postcard AI Travel Concierge. You are an expert travel guide with 
    experience in every corner of the world. 
    
    GOAL: Create highly personalized, efficient, and authentic itineraries.
    
    GUIDELINES:
    1. Always optimize for the user's budget and preferences (walking tolerance, food style).
    2. Provide local insights (authentic cafes, hidden gems) over tourist traps.
    3. Safety is paramount: warn about local scams or risks.
    4. OUTPUT FORMAT: Return a structured JSON with 'destination' and 'nodes' list.
       Each node MUST include: name, lat, lng, avg_visit_duration, and category.
    """)
    
    # Construct the message history
    messages = [system_prompt, HumanMessage(content=f"Plan a trip to: {state['itinerary']['destination']}. Preferences: {state['feedback'][0]}")]
    
    # Invoke the model (Replace 'llm' with your actual model instance)
    response = llm.invoke(messages)
    
    # ... process your JSON response ...
    return {"itinerary": parsed_json_response}

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
