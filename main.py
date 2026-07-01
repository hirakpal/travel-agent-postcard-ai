import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import yaml
from yaml.loader import SafeLoader
from graph import app  # Ensure your LangGraph 'app' is imported from graph.py

# --- 1. Authentication Setup ---
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# --- 2. Page Configuration ---
st.set_page_config(page_title="Postcard AI", layout="wide")
name, authentication_status, username = authenticator.login(location='main')

if authentication_status:
    st.title("Postcard AI: Collaborative Travel Orchestrator")
    st.sidebar.write(f"Logged in as: *{username}*")
    authenticator.logout('Logout', 'sidebar')

    # Initialize session state for concurrency
    if 'seq' not in st.session_state: st.session_state.seq = 0

    # Sidebar Inputs
    with st.sidebar:
        destination = st.text_input("Destination", "Goa")
        feedback = st.text_area("Preferences", "Sunset cafes, beach hotels")
        if st.button("Generate/Update Plan"):
            st.session_state.seq += 1
            initial_state = {
                "itinerary": {"destination": destination, "nodes": []},
                "last_check_timestamp": 0,
                "last_update_seq": st.session_state.seq,
                "feedback": [feedback, f"Updated by {username}"]
            }
            with st.spinner("Orchestrating state..."):
                st.session_state.last_result = app.invoke(initial_state)

    # Output Display
    if 'last_result' in st.session_state:
        res = st.session_state.last_result
        st.success(f"Latest Plan Sequence: {res.get('last_update_seq')}")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.write(f"### {res['itinerary']['destination']}")
            for node in res['itinerary'].get('nodes', []):
                st.write(f"- {node['name']}")
        with col2:
            if res['itinerary'].get('nodes'):
                st.map(pd.DataFrame(res['itinerary']['nodes']))

elif authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status == None:
    st.warning('Please enter your credentials to access the planner.')
