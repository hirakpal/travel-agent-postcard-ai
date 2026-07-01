from typing import TypedDict, List, Annotated
import operator
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

class AgentState(TypedDict):
    messages: Annotated[List, operator.add]
    is_complete: bool

llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

def supervisor_node(state: AgentState):
    # This node analyzes the conversation and decides the next step
    system_prompt = SystemMessage(content="""
    You are a travel concierge. 
    1. If the user hasn't provided Destination, Budget, Dates, and Preferences, ask ONE follow-up question.
    2. If you have all details, generate a JSON itinerary with 4 combinations.
    3. If generating the itinerary, prefix your response with "FINAL_PLAN:" followed by the JSON.
    """)
    
    response = llm.invoke(state['messages'] + [system_prompt])
    
    if "FINAL_PLAN:" in response.content:
        return {"messages": [response], "is_complete": True}
    return {"messages": [response], "is_complete": False}

# Build the Graph
builder = StateGraph(AgentState)
builder.add_node("supervisor", supervisor_node)
builder.set_entry_point("supervisor")

# Conditional edge: If complete, go to END, otherwise loop back
builder.add_conditional_edges("supervisor", lambda x: "end" if x['is_complete'] else "supervisor", {"end": END, "supervisor": "supervisor"})

app = builder.compile()
