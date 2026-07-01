import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import sqlite3
from graph import app  # Your compiled LangGraph

# --- 1. Database & Auth Setup ---
def get_users_from_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # 1. Create table if it doesn't exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (username TEXT PRIMARY KEY, name TEXT, password TEXT)''')
    
    # 2. Check if admin exists; if not, add it
    cursor.execute("SELECT count(*) FROM users WHERE username='admin'")
if cursor.fetchone()[0] == 0:
        import streamlit_authenticator as stauth
        # Corrected: Instantiate Hasher with no arguments
        hasher = stauth.Hasher()
        # Corrected: Pass the list of passwords to the .generate() method
        hashed_password = hasher.generate(['admin123'])[0]
        
        cursor.execute("INSERT INTO users VALUES (?, ?, ?)", 
                       ('admin', 'Administrator', hashed_password))
        conn.commit()
        
    cursor.execute("SELECT username, name, password FROM users")
    users = {row[0]: {'name': row[1], 'password': row[2]} for row in cursor.fetchall()}
    conn.close()
    return users

credentials = {"usernames": get_users_from_db()}
authenticator = stauth.Authenticate(credentials, 'postcard_cookie', 'secret_key', 30)

# --- 2. Page Config ---
st.set_page_config(page_title="Postcard AI", layout="wide")

# --- 3. Login Logic ---
authenticator.login()

if st.session_state["authentication_status"]:
    st.title("Postcard AI: Collaborative Travel Orchestrator")
    st.sidebar.write(f"Logged in as: *{st.session_state['username']}*")
    authenticator.logout('Logout', 'sidebar')

    if 'seq' not in st.session_state: st.session_state.seq = 0

    # --- Collaborative UI ---
    with st.sidebar:
        st.header("Trip Planner")
        destination = st.text_input("Destination", "Goa")
        feedback = st.text_area("Preferences", "Sunset cafes, beach hotels")
        
        if st.button("Generate/Update Plan"):
            st.session_state.seq += 1
            # State includes current username to trace who made the edit
            initial_state = {
                "itinerary": {"destination": destination, "nodes": []},
                "last_check_timestamp": 0,
                "last_update_seq": st.session_state.seq,
                "feedback": [feedback, f"Edit by {st.session_state['username']}"]
            }
            with st.spinner("Orchestrating state..."):
                st.session_state.last_result = app.invoke(initial_state)

    # --- Results & Visualizations ---
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
                st.map(pd.DataFrame(res['itinerary'].get('nodes')))

elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your credentials to access the planner.')

# --- 4. Password Recovery / Register UI ---
with st.expander("Need help with your account?"):
    st.write("Contact the administrator to reset credentials or create a new account.")
