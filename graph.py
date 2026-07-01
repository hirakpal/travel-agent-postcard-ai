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
    You are an expert AI Travel Concierge. 
    Return ONLY a valid JSON object with a "combinations" key containing 4 plans.
    Include 'name', 'days' (with 'day', 'plan', 'insight', 'transport', 'lat', 'lon'), 
    and 'travel_logistics'.
    """)
    
    # 1. Prepare the messages
    messages = [
        system_prompt, 
        HumanMessage(content=f"Plan trip to: {state['itinerary']['destination']} with logistics: {state.get('logistics')}")
    ]
    
    # 2. Invoke the LLM
    response = llm.invoke(messages)
    
    # 3. Parse the data (This creates the 'parsed_data' variable)
    try:
        clean_json = response.content.replace("```json", "").replace("```", "").strip()
        parsed_data = json.loads(clean_json)
    except Exception as e:
        # Fallback if JSON parsing fails
        parsed_data = {"combinations": []}
    
    # 4. Return AFTER the variable is guaranteed to exist
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
