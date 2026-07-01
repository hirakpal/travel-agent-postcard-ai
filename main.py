import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import sqlite3
from graph import app

# --- 1. Robust Schema-Aware DB Initialization ---
def get_users_from_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # Self-Healing: Check if table matches current 4-column requirement
    cursor.execute("PRAGMA table_info(users)")
    if len(cursor.fetchall()) != 4: 
        cursor.execute("DROP TABLE IF EXISTS users")
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (username TEXT PRIMARY KEY, name TEXT, password TEXT, email TEXT)''')
    
    # Bootstrap Admin
    cursor.execute("SELECT count(*) FROM users WHERE username='admin'")
    if cursor.fetchone()[0] == 0:
        hashed = stauth.Hasher().hash('admin123')
        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)", ('admin', 'Administrator', hashed, 'admin@postcard.ai'))
        conn.commit()
    
    cursor.execute("SELECT username, name, password FROM users")
    users = {row[0]: {'name': row[1], 'password': row[2]} for row in cursor.fetchall()}
    conn.close()
    return users

authenticator = stauth.Authenticate({"usernames": get_users_from_db()}, 'cookie', 'key', 30)

# --- 2. Navigation Routing ---
if 'page' not in st.session_state: st.session_state.page = 'login'

def go_to(page):
    st.session_state.page = page
    st.rerun()

# --- 3. UI Logic ---
if st.session_state.page == 'login':
    authenticator.login()
    if st.session_state.get("authentication_status"):
        go_to('app')
    col1, col2 = st.columns(2)
    if col1.button("Sign Up"): go_to('signup')
    if col2.button("Account Recovery"): go_to('recovery')

elif st.session_state.page == 'signup':
    st.header("Sign Up")
    new_user, new_name = st.text_input("Username"), st.text_input("Full Name")
    new_email, new_pass = st.text_input("Email"), st.text_input("Password", type="password")
    if st.button("Register"):
        try:
            conn = sqlite3.connect('users.db')
            hashed = stauth.Hasher().hash(new_pass)
            conn.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (new_user, new_name, hashed, new_email))
            conn.commit()
            conn.close()
            st.success("Account created!")
        except: st.error("Registration failed.")
    if st.button("Back to Login"): go_to('login')

elif st.session_state.page == 'app':
    st.title("Postcard AI")
    if st.sidebar.button("Logout"):
        st.session_state.authentication_status = None
        go_to('login')
        
    username = st.session_state.get('username')
    with st.sidebar:
        dest = st.text_input("Destination", "Goa")
        feed = st.text_area("Preferences", "Sunset cafes, beach hotels")
        if st.button("Generate Plan"):
            st.session_state.seq = st.session_state.get('seq', 0) + 1
            # FIXED: Full state initialization (prevents KeyError)
            st.session_state.last_result = app.invoke({
                "itinerary": {"destination": dest, "nodes": []},
                "last_update_seq": st.session_state.seq,
                "last_check_timestamp": 0.0,
                "feedback": [feed, f"Edit by {username}"]
            })
    
    if 'last_result' in st.session_state:
        st.map(pd.DataFrame(st.session_state.last_result['itinerary'].get('nodes')))
