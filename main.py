import streamlit as st
import pandas as pd
from graph import app  # Imports the compiled LangGraph from graph.py

# --- Page Configuration ---
st.set_page_config(page_title="Postcard AI", layout="wide")
st.title("Postcard AI: Your Smart Travel Planner")

# --- Initialize Session State for Concurrency Control ---
if 'seq' not in st.session_state:
    st.session_state.seq = 0

# --- Sidebar Inputs ---
with st.sidebar:
    st.header("Trip Configuration")
    destination = st.text_input("Destination", "Udaipur")
    feedback = st.text_area("Preferences", "Quiet, lake-side stays")
    generate_btn = st.button("Generate Itinerary")

# --- Agent Execution Logic ---
if generate_btn:
    st.session_state.seq += 1  # Increment sequence for concurrency control
    
    # Define initial state
    initial_state = {
        "itinerary": {"destination": destination, "nodes": []},
        "last_check_timestamp": 0, 
        "last_update_seq": st.session_state.seq,
        "feedback": [feedback]
    }
    
    try:
        with st.spinner("Agent is orchestrating your plan..."):
            # Invoking the compiled LangGraph app
            result = app.invoke(initial_state)
            st.session_state.last_result = result
            
        st.success(f"Plan generated! (Sequence: {result.get('last_update_seq')})")
    except Exception as e:
        st.error(f"Agent encountered an error: {e}")

# --- Output Display & Map Visualization ---
if 'last_result' in st.session_state:
    res = st.session_state.last_result
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader(f"Trip to {res['itinerary']['destination']}")
        st.write("**Recommended Nodes:**")
        for node in res['itinerary'].get('nodes', []):
            st.write(f"- {node['name']}")
            
    with col2:
        # Visualize nodes on the map
        nodes = res['itinerary'].get('nodes', [])
        if nodes:
            try:
                # Convert list of Location objects to DataFrame for st.map
                map_data = pd.DataFrame(nodes)
                # Ensure columns are named 'lat' and 'lon' for st.map
                st.subheader("Interactive Route Map")
                st.map(map_data)
            except Exception as e:
                st.info("Ensure the LLM output includes lat/lon for map visualization.")
