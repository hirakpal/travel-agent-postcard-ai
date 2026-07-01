import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import sqlite3
import secrets
import smtplib
import folium
from streamlit_folium import st_folium
from graph import app
from email.message import EmailMessage

# --- 1. Database & Authentication ---
def get_users_from_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, name TEXT, password TEXT, email TEXT)")
    cursor.execute("SELECT username, name, password FROM users")
    users = {row[0]: {'name': row[1], 'password': row[2]} for row in cursor.fetchall()}
    conn.close()
    return users

# --- 2. UI Configuration ---
st.set_page_config(layout="wide")
if 'page' not in st.session_state: st.session_state.page = 'login'

authenticator = stauth.Authenticate({"usernames": get_users_from_db()}, 'cookie', 'key', 30)

def go_to(page): st.session_state.page = page; st.rerun()

# --- 3. Page Logic ---
if st.session_state.page == 'login':
    authenticator.login()
    if st.session_state.get("authentication_status"): go_to('app')
    if st.button("Sign Up"): go_to('signup')

elif st.session_state.page == 'app':
    st.title("Postcard AI Travel Concierge")
    
    with st.sidebar:
        st.header("Trip Configuration")
        dest = st.text_input("Destination", key="destination_input")
        budget = st.slider("Budget Range (₹)", 10000, 500000, 50000)
        mode = st.selectbox("How are you reaching?", ["Flight", "Bus", "Driving"])
        
        if mode == "Driving":
            arr_date = st.date_input("Arrival Date")
            dep_date = st.date_input("Departure Date")
            logistics = {"mode": mode, "budget": budget, "arr": str(arr_date), "dep": str(dep_date)}
        else:
            t_date = st.date_input("Travel Date")
            logistics = {"mode": mode, "budget": budget, "date": str(t_date)}
            
        feed = st.text_area("Preferences")
        
        if st.button("Curate 4 Trip Combinations"):
            st.session_state.last_result = app.invoke({
                "itinerary": {"destination": dest},
                "logistics": logistics,
                "feedback": [feed]
            })

    if 'last_result' in st.session_state:
        data = st.session_state.last_result.get('itinerary', {})
        combinations = data.get('combinations', [])
        
        if combinations:
            tabs = st.tabs([c['name'] for c in combinations])
            for i, tab in enumerate(tabs):
                with tab:
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.subheader(f"Plan: {combinations[i]['name']}")
                        for day in combinations[i].get('days', []):
                            with st.expander(f"Day {day['day']}"):
                                st.write(f"**Plan:** {day['plan']}")
                                st.write(f"**Transport:** {day['transport']}")
                    with col2:
                        st.subheader("Itinerary Map")
                        # Note: If your LLM returns nodes for combinations, render them here
                        st.info("Interactive map updates based on selected combination.")
        else:
            st.warning("Generating plans...")
