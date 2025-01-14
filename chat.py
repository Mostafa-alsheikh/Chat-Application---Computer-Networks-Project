import tkinter as tk
from tkinter import messagebox
import socket
import threading
import sqlite3

# Database setup
def initialize_database():
    conn = sqlite3.connect('chat_app.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sender TEXT NOT NULL,
                        receiver TEXT NOT NULL,
                        message TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS groups (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS group_members (
                        group_id INTEGER NOT NULL,
                        username TEXT NOT NULL,
                        FOREIGN KEY(group_id) REFERENCES groups(id)
                    )''')
    conn.commit()
    conn.close()

# Save message to the database
def save_message(sender, receiver, message):
    conn = sqlite3.connect('chat_app.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO messages (sender, receiver, message) VALUES (?, ?, ?)', (sender, receiver, message))
    conn.commit()
    conn.close()

# Retrieve old messages for a user
def get_user_messages(username):
    conn = sqlite3.connect('chat_app.db')
    cursor = conn.cursor()
    cursor.execute('SELECT sender, message, timestamp FROM messages WHERE receiver = ? ORDER BY timestamp', (username,))
    messages = cursor.fetchall()
    conn.close()
    return messages

# Create a group
def create_group(group_name, members):
    conn = sqlite3.connect('chat_app.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO groups (name) VALUES (?)', (group_name,))
    group_id = cursor.lastrowid
    cursor.executemany('INSERT INTO group_members (group_id, username) VALUES (?, ?)', [(group_id, member) for member in members])
    conn.commit()
    conn.close()

# Get group members
def get_group_members(group_name):
    conn = sqlite3.connect('chat_app.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM groups WHERE name = ?', (group_name,))
    group_id = cursor.fetchone()
    if not group_id:
        return []
    group_id = group_id[0]
    cursor.execute('SELECT username FROM group_members WHERE group_id = ?', (group_id,))
    members = [row[0] for row in cursor.fetchall()]
    conn.close()
    return members

# Add this new function to check if user exists and get their messages
def get_user_history(username):
    conn = sqlite3.connect('chat_app.db')
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT sender FROM messages WHERE sender = ?', (username,))
    exists = cursor.fetchone() is not None
    messages = []
    if exists:
        cursor.execute('''
            SELECT sender, receiver, message, timestamp 
            FROM messages 
            WHERE sender = ? OR receiver = ?
            ORDER BY timestamp
        ''', (username, username))
        messages = cursor.fetchall()
    conn.close()
    return exists, messages

# Server code
def handle_client(client_socket, client_address, clients, users):
    try:
        client_socket.send("Enter your username: ".encode())
        username = client_socket.recv(1024).decode().strip()

        if not username or username in users:
            client_socket.send("Invalid or already-taken username. Connection closing.\n".encode())
            client_socket.close()
            return

        users[username] = client_socket

        # Send old messages to the user
        old_messages = get_user_messages(username)
        if old_messages:
            client_socket.send("Your previous messages:\n".encode())
            for sender, message, timestamp in old_messages:
                client_socket.send(f"[{timestamp}] {sender}: {message}\n".encode())

        client_socket.send(f"Welcome, {username}! Commands:\n/to <username> <message>\n/to group:<groupname> <message>\n/group <groupname> <user1> <user2> ...\n".encode())
        print(f"{username} connected from {client_address}")

        while True:
            msg = client_socket.recv(1024).decode()
            if msg.lower() == 'exit':
                break

            if msg.startswith("/to "):
                try:
                    target, message = msg[4:].split(" ", 1)
                    if target.startswith("group:"):
                        group_name = target[6:]
                        members = get_group_members(group_name)
                        if not members:
                            client_socket.send(f"Group '{group_name}' not found.\n".encode())
                        elif username not in members:
                            client_socket.send(f"You are not a member of group '{group_name}'.\n".encode())
                        else:
                            # Send message to all online group members
                            for member in members:
                                if member in users and member != username:
                                    users[member].send(f"[Group {group_name}] {username}: {message}\n".encode())
                            # Send confirmation to sender
                            client_socket.send(f"[Group {group_name}] Message sent.\n".encode())
                            # Save message with group prefix
                            save_message(username, f"group:{group_name}", message)
                    elif target in users:
                        users[target].send(f"{username}: {message}\n".encode())
                        save_message(username, target, message)
                    else:
                        client_socket.send(f"User '{target}' not found.\n".encode())
                except ValueError:
                    client_socket.send("Invalid message format. Use /to <username|group:group_name> <message>\n".encode())
            elif msg.startswith("/group "):
                try:
                    parts = msg[7:].split()
                    if len(parts) < 2:
                        client_socket.send("Invalid group format. Use /group <groupname> <user1> <user2> ...\n".encode())
                        continue
                        
                    group_name = parts[0]
                    members = list(set(parts[1:] + [username]))  # Add creator and remove duplicates
                    
                    # Verify all users exist
                    invalid_users = [user for user in members if user not in users and user != username]
                    if invalid_users:
                        client_socket.send(f"Some users not found: {', '.join(invalid_users)}\n".encode())
                        continue
                    
                    create_group(group_name, members)
                    
                    # Notify all online group members
                    for member in members:
                        if member in users:
                            users[member].send(f"You've been added to group '{group_name}' (Members: {', '.join(members)})\n".encode())
                            
                except sqlite3.IntegrityError:
                    client_socket.send(f"Group '{group_name}' already exists.\n".encode())
                except Exception as e:
                    client_socket.send(f"Error creating group: {str(e)}\n".encode())
            else:
                client_socket.send("Unknown command. Use:\n/to <username> <message>\n/to group:<groupname> <message>\n/group <groupname> <user1> <user2> ...\n".encode())
    except Exception as e:
        print(f"Error handling client {client_address}: {e}")
    finally:
        if username in users:
            del users[username]
        client_socket.close()


def start_server(host='127.0.0.1', port=12345):
    initialize_database()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Server running on {host}:{port}")

    users = {}

    while True:
        client_socket, client_address = server_socket.accept()
        client_thread = threading.Thread(
            target=handle_client, 
            args=(client_socket, client_address, None, users)
        )
        client_thread.start()

# Modify the client code to show message history
def start_client(host='127.0.0.1', port=12345):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    # Create client window
    client_window = tk.Tk()
    client_window.title("Chat Client")
    client_window.geometry("600x400")

    # Create text area for messages
    messages_area = tk.Text(client_window, height=20, width=60)
    messages_area.pack(pady=10)
    messages_area.config(state='disabled')

    # Create input field
    input_field = tk.Entry(client_window, width=50)
    input_field.pack(pady=10)

    def send_message(event=None):
        msg = input_field.get()
        if msg.lower() == 'exit':
            client_window.quit()
        else:
            client_socket.send(msg.encode())
            input_field.delete(0, tk.END)

    # Bind enter key to send message
    input_field.bind("<Return>", send_message)
    
    # Send button
    send_button = tk.Button(client_window, text="Send", command=send_message)
    send_button.pack()

    def receive_messages():
        while True:
            try:
                message = client_socket.recv(1024).decode()
                if not message:
                    break
                messages_area.config(state='normal')
                messages_area.insert(tk.END, message + "\n")
                messages_area.see(tk.END)
                messages_area.config(state='disabled')
                
                # Check if this is the username prompt
                if message.startswith("Enter your username:"):
                    username = input_field.get()
                    exists, history = get_user_history(username)
                    if exists:
                        messages_area.config(state='normal')
                        messages_area.insert(tk.END, "--- Previous Messages ---\n")
                        for msg in history:
                            messages_area.insert(tk.END, f"[{msg[3]}] {msg[0]} -> {msg[1]}: {msg[2]}\n")
                        messages_area.insert(tk.END, "--- End of History ---\n")
                        messages_area.config(state='disabled')
            except Exception as e:
                print(f"Error receiving message: {e}")
                break

    threading.Thread(target=receive_messages, daemon=True).start()
    client_window.mainloop()
    client_socket.close()

# Modify the main function to use GUI
def main():
    root = tk.Tk()
    root.title("Chat Application")
    root.geometry("300x200")

    def start_application(role):
        root.destroy()
        if role == "server":
            start_server()
        else:
            start_client()

    tk.Label(root, text="Select Role", font=('Arial', 14)).pack(pady=20)
    
    server_btn = tk.Button(root, text="Start Server", 
                          command=lambda: start_application("server"),
                          width=20, height=2)
    server_btn.pack(pady=10)
    
    client_btn = tk.Button(root, text="Start Client", 
                          command=lambda: start_application("client"),
                          width=20, height=2)
    client_btn.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()
