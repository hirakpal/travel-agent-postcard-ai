import json
import time
from typing import TypedDict, List, Annotated
import operator
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

class AgentState(TypedDict):
    itinerary: dict
    last_check_timestamp: float
    last_update_seq: int
    feedback: Annotated[List[str], operator.add]

llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

def planning_node(state: AgentState):
    system_prompt = SystemMessage(content="""
    You are an expert travel guide. 
    1. Identify real, specific tourist attractions in the destination.
    2. Provide ACCURATE latitude and longitude for each specific place, not just the city center.
    3. Return ONLY a JSON object: {"destination": "...", "nodes": [{"name": "...", "lat": ..., "lng": ..., "category": "..."}]}
    """)
    messages = [system_prompt, HumanMessage(content=f"Plan trip to: {state['itinerary']['destination']}. Feedback: {state.get('feedback', [''])[0]}")]
    
    response = llm.invoke(messages)
    try:
        parsed_data = json.loads(response.content.replace("```json", "").replace("```", "").strip())
    except:
        parsed_data = {"destination": state['itinerary']['destination'], "nodes": []}
    return {"itinerary": parsed_data, "last_check_timestamp": time.time()}

builder = StateGraph(AgentState)
builder.add_node("planner", planning_node)
builder.set_entry_point("planner")
builder.add_edge("planner", END)
app = builder.compile()
