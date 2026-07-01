import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import sqlite3
from graph import app

# --- Database Helpers ---
def get_users_from_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, name, password FROM users")
    users = {row[0]: {'name': row[1], 'password': row[2]} for row in cursor.fetchall()}
    conn.close()
    return users

# --- Authentication Setup ---
authenticator = stauth.Authenticate({"usernames": get_users_from_db()}, 'cookie', 'key', 30)

st.set_page_config(page_title="Postcard AI", layout="wide")

# --- UI Management ---
tab1, tab2, tab3 = st.tabs(["Login", "Sign Up", "Account Recovery"])

with tab1:
    authenticator.login()
    if st.session_state.get("authentication_status"):
        st.write(f"Welcome, {st.session_state['username']}!")
        # [Insert your existing App Logic here...]

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
            st.success("Account created! Please log in.")
        except sqlite3.IntegrityError:
            st.error("Username already exists.")

with tab3: # Recovery
    st.write("Forgot Login ID or Password?")
    rec_email = st.text_input("Enter your registered email")
    if st.button("Request Recovery"):
        st.info("Check your inbox for a reset token (Simulated).")

#
