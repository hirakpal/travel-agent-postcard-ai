import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import sqlite3
import secrets
import smtplib
from email.message import EmailMessage
from graph import app

# --- Helper Functions ---
def get_users_from_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, name TEXT, password TEXT, email TEXT)")
    cursor.execute("SELECT username, name, password FROM users")
    users = {row[0]: {'name': row[1], 'password': row[2]} for row in cursor.fetchall()}
    conn.close()
    return users

# --- Main App Logic ---
st.set_page_config(layout="wide") # Wider layout for better map visibility
if 'page' not in st.session_state: st.session_state.page = 'login'

# [Authentication and Recovery Logic Remains Same as Previous Version]

if st.session_state.page == 'app':
    st.title("Postcard AI Travel Concierge")
    
    with st.sidebar:
        st.header("Plan your trip")
        dest = st.text_input("Destination")
        t_date = st.date_input("Travel Date")
        feed = st.text_area("Preferences")
        if st.button("Generate Plan"):
            st.session_state.last_result = app.invoke({
                "itinerary": {"destination": dest, "nodes": []},
                "travel_date": str(t_date),
                "feedback": [feed]
            })
        if st.button("Logout"): st.rerun()

    if 'last_result' in st.session_state:
        nodes = st.session_state.last_result['itinerary'].get('nodes', [])
        if nodes:
            col1, col2 = st.columns([1, 1])
            with col1:
                st.subheader("Curated Recommendations")
                for node in nodes:
                    status = "✅ Open" if node.get('is_open_on_date') else "❌ Closed"
                    with st.expander(f"{node.get('name')} {status}"):
                        st.write(f"**Category:** {node.get('category')}")
                        st.write(f"**Weekday:** {node.get('weekday_hours')}")
                        st.write(f"**Weekend:** {node.get('weekend_hours')}")
            with col2:
                st.subheader("Itinerary Map")
                df = pd.DataFrame(nodes)
                if 'lng' in df.columns: df = df.rename(columns={'lng': 'lon'})
                if 'lat' in df.columns: st.map(df)
