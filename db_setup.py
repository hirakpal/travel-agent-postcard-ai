import sqlite3
import streamlit_authenticator as stauth

# Initialize database
conn = sqlite3.connect('users.db')
c = conn.cursor()

# Create users table
c.execute('''CREATE TABLE IF NOT EXISTS users
             (username TEXT PRIMARY KEY, name TEXT, password TEXT)''')

# Example: Add an admin user (Password: admin123)
hashed_password = stauth.Hasher(['admin123']).generate()[0]
c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?)", 
          ('admin', 'Administrator', hashed_password))

conn.commit()
conn.close()
print("Database initialized successfully.")
