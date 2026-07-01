import sqlite3
import streamlit_authenticator as stauth

def initialize_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    # Added 'email' for account recovery
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, name TEXT, password TEXT, email TEXT)''')
    
    # Initialize admin if empty
    c.execute("SELECT count(*) FROM users WHERE username='admin'")
    if c.fetchone()[0] == 0:
        hashed = stauth.Hasher().hash('admin123')
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?)", 
                  ('admin', 'Administrator', hashed, 'admin@postcard.ai'))
        conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_db()
    print("Database initialized with recovery schema.")
