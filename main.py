import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import sqlite3
from graph import app

# --- 1. Database & Schema Management ---
def get_users_from_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # Schema check: Drop if columns don't match (prevents the 3 vs 4 column error)
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    if len(columns) > 0 and len(columns) != 4:
        cursor.execute("DROP TABLE users")
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (username TEXT PRIMARY KEY, name TEXT, password TEXT, email TEXT)''')
    
    # Initialize Admin
    cursor.execute("SELECT count(*) FROM users WHERE username='admin'")
    if cursor.fetchone()[0] == 0:
        hashed = stauth.Hasher().hash('admin123')
        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)", ('admin', 'Administrator', hashed, 'admin@postcard.ai'))
        conn.commit()
        
    cursor.execute("SELECT username, name, password FROM users")
    users = {row[0]: {'name': row[1], 'password': row[2]} for row in cursor.fetchall()}
    conn.close()
    return users

# --- 2. Auth & Config ---
authenticator = stauth.Authenticate({"usernames": get_users_from_db()}, 'cookie', 'key', 30)
st.set_page_config(page_title="Postcard AI", layout="wide")

# --- 3. App UI ---
tab1, tab2, tab3 = st.tabs(["Login", "Sign Up", "Account Recovery"])

with tab1:
    authenticator.login()
    if st.session_state.get("authentication_status"):
        st.title("Postcard AI: Collaborative Travel Orchestrator")
        st.sidebar.write(f"Logged in as: *{st.session_state['username']}*")
        authenticator.logout('Logout', 'sidebar')

        if 'seq' not in st.session_state: st.session_state.seq = 0
        with st.sidebar:
            dest = st.text_input("Destination", "Goa")
            feed = st.text_area("Preferences", "Sunset cafes, beach hotels")
            if st.button("Generate Plan"):
                st.session_state.seq += 1
                st.session_state.last_result = app.invoke({
                    "itinerary": {"destination": dest, "nodes": []},
                    "last_update_seq": st.session_state.seq,
                    "feedback": [feed, f"Edit by {st.session_state['username']}"]
                })

        if 'last_result' in st.session_state:
            res = st.session_state.last_result
            col1, col2 = st.columns(2)
            with col1:
                for node in res['itinerary'].get('nodes', []): st.write(f"- {node['name']}")
            with col2:
                st.map(pd.DataFrame(res['itinerary'].get('nodes')))

with tab2: # Sign Up
    new_user = st.text_input("New Username")
    new_name = st.text_input("Full Name")
    new_email = st.text_input("Email")
    new_pass = st.text_input("Password", type="password")
    if st.button("Register"):
        try:
            conn = sqlite3.connect('users.db')
            hashed = stauth.Hasher().hash(new_pass)
            conn.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (new_user, new_name, hashed, new_email))
            conn.commit()
            conn.close()
            st.success("Account created!")
        except Exception as e:
            st.error("Registration failed. Username may already exist.")

with tab3:
    st.info("Contact admin to reset credentials.")
