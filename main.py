import streamlit as st
import streamlit_authenticator as stauth
import sqlite3
import folium
from streamlit_folium import st_folium
from graph import app

st.set_page_config(layout="wide")

# --- 1. Database & Auth ---
def get_users_from_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, name TEXT, password TEXT, email TEXT, avatar TEXT)")
    cursor.execute("SELECT username, name, password FROM users")
    users = {row[0]: {'name': row[1], 'password': row[2]} for row in cursor.fetchall()}
    conn.close()
    return users

# --- 2. Logic ---
if 'page' not in st.session_state: st.session_state.page = 'login'
authenticator = stauth.Authenticate({"usernames": get_users_from_db()}, 'cookie', 'key', 30)

if st.session_state.page == 'login':
    if authenticator.login():
        st.session_state.page = 'app'
        st.rerun()

elif st.session_state.page == 'app':
    # --- Personalized Sidebar ---
    name = st.session_state.get('name', 'Traveler')
    with st.sidebar:
        st.title(f"Hello, {name}!")
        avatar = st.radio("Pick your Avatar", ["👤", "✈️", "🌍", "📸"], horizontal=True)
        st.markdown(f"## {avatar}")
        
        st.header("Trip Configuration")
        dest = st.text_input("Destination", key="dest_input")
        budget = st.slider("Budget (₹)", 10000, 500000, 50000, key="budget_slider")
        mode = st.selectbox("Mode", ["Flight", "Bus", "Driving"], key="mode_select")
        
        if st.button("Curate 4 Combinations"):
            st.session_state.last_result = app.invoke({
                "itinerary": {"destination": dest},
                "logistics": {"mode": mode, "budget": budget}
            })
        if st.button("Logout"): st.session_state.page = 'login'; st.rerun()

    # --- Personalized Dashboard ---
    if 'last_result' in st.session_state:
        combinations = st.session_state.last_result['itinerary'].get('combinations', [])
        if combinations:
            tabs = st.tabs([c['name'] for c in combinations])
            for i, tab in enumerate(tabs):
                with tab:
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        for day in combinations[i].get('days', []):
                            with st.expander(f"Day {day['day']}"):
                                st.write(f"**Plan:** {day['plan']}")
                                st.write(f"**Transport:** {day['transport']}")
                    with col2:
                        st.subheader("Interactive Logistics")
                        st.info(f"Logistics Suggestion: {combinations[i]['travel_logistics']['suggestion']}")
        else:
            st.warning("Generating your travel combinations...")
