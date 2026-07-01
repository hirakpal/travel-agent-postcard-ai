import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import sqlite3
import secrets
import smtplib
import folium
from streamlit_folium import st_folium
from email.message import EmailMessage
from graph import app

# --- 1. Database & Authentication ---
def get_users_from_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, name TEXT, password TEXT, email TEXT)")
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
        msg.set_content(f"Your recovery token: {token}\nEnter this code on the Account Recovery page.")
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

# --- 3. UI Configuration & Routing ---
st.set_page_config(layout="wide")

if 'page' not in st.session_state: st.session_state.page = 'login'
if 'recovery_tokens' not in st.session_state: st.session_state.recovery_tokens = {}

authenticator = stauth.Authenticate({"usernames": get_users_from_db()}, 'cookie', 'key', 30)

def go_to(page): st.session_state.page = page; st.rerun()

# --- 4. Page Logic ---
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
        conn = sqlite3.connect('users.db')
        conn.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (u, n, stauth.Hasher().hash(p), e))
        conn.commit(); conn.close()
        st.success("Account created!")
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
            conn.execute("UPDATE users SET password=? WHERE username=?", (stauth.Hasher().hash(new_p), st.session_state.recovery_tokens[t_in]))
            conn.commit(); conn.close()
            del st.session_state.recovery_tokens[t_in]
            st.success("Password updated!")
        else: st.error("Invalid token.")
    if st.button("Back to Login"): go_to('login')

elif st.session_state.page == 'app':
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
            st.session_state.selected_node = None 
        if st.button("Logout"): 
            st.session_state.authentication_status = None
            go_to('login')

    if 'last_result' in st.session_state:
        nodes = st.session_state.last_result['itinerary'].get('nodes', [])
        if nodes:
            col1, col2 = st.columns([1, 1])
            with col1:
                st.subheader("Curated Recommendations")
                for node in nodes:
                    status = "✅ Open" if node.get('is_open_on_date') else "❌ Closed"
                    if st.button(f"View {node.get('name')}", key=node.get('name')):
                        st.session_state.selected_node = node
                    with st.expander(f"{node.get('name')} {status}"):
                        st.write(f"**Category:** {node.get('category')}")
                        st.write(f"**Weekday:** {node.get('weekday_hours')}")
            with col2:
                st.subheader("Itinerary Map")
                m = folium.Map(location=[nodes[0]['lat'], nodes[0]['lng']], zoom_start=13)
                for node in nodes:
                    is_selected = 'selected_node' in st.session_state and st.session_state.selected_node and st.session_state.selected_node['name'] == node['name']
                    folium.Marker(
                        [node['lat'], node['lng']], 
                        popup=node['name'],
                        icon=folium.Icon(color="blue" if is_selected else "red")
                    ).add_to(m)
                st_folium(m, width=700, height=500)
