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

import json
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage

def planning_node(state: AgentState):
    # 1. Define the prompt
    system_prompt = SystemMessage(content="""
    You are an expert Travel Concierge. Return ONLY a valid JSON object:
    {
      "combinations": [{
        "name": "Luxury Relaxed",
        "days": [{"day": 1, "plan": "...", "insight": "...", "transport": "...", "lat": 0.0, "lon": 0.0}],
        "travel_logistics": {"suggestion": "...", "estimated_cost": 0}
      }]
    }
    """)
    
    # 2. Build the messages
    messages = [
        system_prompt, 
        HumanMessage(content=f"Plan trip to: {state['itinerary'].get('destination')} with logistics: {state.get('logistics')}")
    ]
    
    # 3. Call the LLM
    response = llm.invoke(messages)
    
    # 4. Parse the response (THIS defines parsed_data)
    try:
        clean_json = response.content.replace("```json", "").replace("```", "").strip()
        parsed_data = json.loads(clean_json)
    except Exception:
        # Fallback if LLM fails
        parsed_data = {"combinations": []}
    
    # 5. Return the result AFTER the variable is defined
    return {"itinerary": parsed_data}

builder = StateGraph(AgentState)
builder.add_node("planner", planning_node)
builder.set_entry_point("planner")
builder.add_edge("planner", END)
app = builder.compile()
