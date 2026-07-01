import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import sqlite3
import secrets
import smtplib
from email.message import EmailMessage
from graph import app

# --- 1. Database & Schema Management ---
def get_users_from_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users)")
    if len(cursor.fetchall()) != 4: cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, name TEXT, password TEXT, email TEXT)''')
    cursor.execute("SELECT count(*) FROM users WHERE username='admin'")
    if cursor.fetchone()[0] == 0:
        hashed = stauth.Hasher().hash('admin123')
        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)", ('admin', 'Administrator', hashed, 'admin@postcard.ai'))
        conn.commit()
    cursor.execute("SELECT username, name, password FROM users")
    users = {row[0]: {'name': row[1], 'password': row[2]} for row in cursor.fetchall()}
    conn.close()
    return users

# --- 2. Token Email Helper ---
def send_token_email(recipient, token):
    try:
        sender = st.secrets["EMAIL_USER"]
        password = st.secrets["EMAIL_PASS"]
        msg = EmailMessage()
        msg.set_content(f"Your 8-character recovery token is: {token}\n\nEnter this on the Account Recovery page.")
        msg['Subject'] = 'Your Recovery Token'
        msg['From'] = sender
        msg['To'] = recipient
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(sender, password)
            s.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Email failed: {e}")
        return False

# --- 3. App State & Routing ---
if 'recovery_tokens' not in st.session_state: st.session_state.recovery_tokens = {}
if 'page' not in st.session_state: st.session_state.page = 'login'

authenticator = stauth.Authenticate({"usernames": get_users_from_db()}, 'cookie', 'key', 30)

def go_to(page): st.session_state.page = page; st.rerun()

# --- 4. Main UI Logic ---
if st.session_state.page == 'login':
    authenticator.login()
    if st.session_state.get("authentication_status"): go_to('app')
    if st.button("Sign Up"): go_to('signup')
    if st.button("Account Recovery"): go_to('recovery')

elif st.session_state.page == 'signup':
    st.header("Create Account")
    u, n = st.text_input("Username"), st.text_input("Full Name")
    e, p = st.text_input("Email"), st.text_input("Password", type="password")
    if st.button("Register"):
        try:
            conn = sqlite3.connect('users.db')
            conn.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (u, n, stauth.Hasher().hash(p), e))
            conn.commit(); conn.close()
            st.success("Account created!")
        except: st.error("Registration failed.")
    if st.button("Back to Login"): go_to('login')

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
            conn.execute("UPDATE users SET password=? WHERE username=?", 
                         (stauth.Hasher().hash(new_p), st.session_state.recovery_tokens[t_in]))
            conn.commit(); conn.close()
            del st.session_state.recovery_tokens[t_in] # Token revocation
            st.success("Success! Password updated.")
        else: st.error("Invalid token.")
    if st.button("Back to Login"): go_to('login')

elif st.session_state.page == 'app':
    st.title("Postcard AI")
    if st.sidebar.button("Logout"): st.session_state.authentication_status = None; go_to('login')
    
    with st.sidebar:
        dest, feed = st.text_input("Destination"), st.text_area("Preferences")
        if st.button("Generate Plan"):
            st.session_state.seq = st.session_state.get('seq', 0) + 1
            st.session_state.last_result = app.invoke({
                "itinerary": {"destination": dest, "nodes": []},
                "last_update_seq": st.session_state.seq,
                "last_check_timestamp": 0.0,
                "feedback": [feed, f"Edit by {st.session_state.get('username')}"]
            })
    if 'last_result' in st.session_state:
        st.map(pd.DataFrame(st.session_state.last_result['itinerary'].get('nodes')))
