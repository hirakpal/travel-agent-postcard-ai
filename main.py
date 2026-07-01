import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import sqlite3
import secrets
import smtplib
from email.message import EmailMessage
from graph import app

# --- Database & Schema ---
def get_users_from_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, name TEXT, password TEXT, email TEXT)")
    cursor.execute("SELECT username, name, password FROM users")
    users = {row[0]: {'name': row[1], 'password': row[2]} for row in cursor.fetchall()}
    conn.close()
    return users

# --- Email Helper ---
def send_token_email(recipient, token):
    try:
        sender = st.secrets["EMAIL_USER"]
        password = st.secrets["EMAIL_PASS"]
        msg = EmailMessage()
        msg.set_content(f"Your recovery token: {token}\nEnter this on the Account Recovery page.")
        msg['Subject'] = 'Postcard AI Recovery'
        msg['From'] = sender
        msg['To'] = recipient
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(sender, password)
            s.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Email failed: {e}")
        return False

# --- UI Routing ---
if 'recovery_tokens' not in st.session_state: st.session_state.recovery_tokens = {}
if 'page' not in st.session_state: st.session_state.page = 'login'

authenticator = stauth.Authenticate({"usernames": get_users_from_db()}, 'cookie', 'key', 30)

def go_to(page): st.session_state.page = page; st.rerun()

if st.session_state.page == 'login':
    authenticator.login()
    if st.session_state.get("authentication_status"): go_to('app')
    if st.button("Sign Up"): go_to('signup')
    if st.button("Account Recovery"): go_to('recovery')

elif st.session_state.page == 'recovery':
    st.header("Account Recovery")
    email_in = st.text_input("Registered Email")
    if st.button("Send Token"):
        conn = sqlite3.connect('users.db')
        user = conn.execute("SELECT username FROM users WHERE email=?", (email_in,)).fetchone()
        if user:
            token = secrets.token_hex(4).upper()
            st.session_state.recovery_tokens[token] = user[0]
            if send_token_email(email_in, token): st.success("Token sent!")
        else: st.error("Email not found.")
        conn.close()
    t_in = st.text_input("Enter 8-character Token")
    new_p = st.text_input("New Password", type="password")
    if st.button("Update Password"):
        if t_in in st.session_state.recovery_tokens:
            conn = sqlite3.connect('users.db')
            conn.execute("UPDATE users SET password=? WHERE username=?", (stauth.Hasher().hash(new_p), st.session_state.recovery_tokens[t_in]))
            conn.commit(); conn.close()
            del st.session_state.recovery_tokens[t_in]
            st.success("Password updated!")
        else: st.error("Invalid token.")
    if st.button("Back to Login"): go_to('login')

elif st.session_state.page == 'app':
    st.title("Postcard AI Travel Concierge")
    # ... logout and sidebar code ...

    if 'last_result' in st.session_state:
        nodes = st.session_state.last_result['itinerary'].get('nodes', [])
        if nodes:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("Curated Recommendations")
                for node in nodes:
                    with st.expander(f"{node['name']} ({node['category']})"):
                        st.write(f"Estimated time: {node.get('avg_visit_duration', 60)} mins")
                        # You can add more fields here as the AI adds them
            
            with col2:
                st.subheader("Itinerary Map")
                df = pd.DataFrame(nodes)
                if 'lng' in df.columns: df = df.rename(columns={'lng': 'lon'})
                st.map(df)
    if 'last_result' in st.session_state:
        nodes = st.session_state.last_result['itinerary'].get('nodes', [])
        if nodes:
            df = pd.DataFrame(nodes)
            if 'lng' in df.columns: df = df.rename(columns={'lng': 'lon'})
            st.map(df)
