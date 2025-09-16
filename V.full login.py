import tkinter as tk
from tkinter import messagebox
import mysql.connector

# Database connection function
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",      # Change if not running locally
        user="root",           # Your MySQL username
        password="pass124**",  # Your MySQL password
        database="login_system"   # The database we created
    )

# Function to handle login
def login():
    entered_username = username_entry.get()
    entered_password = password_entry.get()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s",
                   (entered_username, entered_password))
    result = cursor.fetchone()

    if result:
        messagebox.showinfo("Login Success", f"Welcome, {entered_username}!")
    else:
        messagebox.showerror("Login Failed", "Invalid Username or Password!")

    conn.close()

# Function to register a new user
def register():
    entered_username = username_entry.get()
    entered_password = password_entry.get()

    if not entered_username or not entered_password:
        messagebox.showwarning("Input Error", "Username and Password cannot be empty.")
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)",
                       (entered_username, entered_password))
        conn.commit()
        messagebox.showinfo("Registration Success", f"User '{entered_username}' registered successfully!")
    except mysql.connector.IntegrityError:
        messagebox.showerror("Registration Failed", "Username already exists!")
    finally:
        conn.close()

# Main window
root = tk.Tk()
root.title("J_TECH.COM")
root.geometry("350x250")
root.resizable(False, False)


# Username label & entry
tk.Label(root, text="Username:").pack(pady=5)
username_entry = tk.Entry(root, width=30)
username_entry.pack(pady=5)

# Password label & entry
tk.Label(root, text="Password:").pack(pady=5)
password_entry = tk.Entry(root, show="*", width=30)
password_entry.pack(pady=5)

# Buttons
tk.Button(root, text="Login", command=login, width=15, bg="blue", fg="white").pack(pady=10)
tk.Button(root, text="Register", command=register, width=15, bg="green", fg="white").pack(pady=5)

# Run the application
root.mainloop()
