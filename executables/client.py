import asyncio
import websockets
import ssl
import tkinter as tk
import threading
import queue
from tkinter import filedialog
import os
import json

SERVER_URI = "wss://lg09dxfj-443.usw3.devtunnels.ms/:443"
message_queue = queue.Queue()
send_queue = None
asyncio_loop = None
websocket_ref = None 
current_target = None 

import datetime

LOG_FILE = "client_chat_log.txt"

def set_client_log(username: str):
    global LOG_FILE
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if not os.path.exists("clientlogs"):
        os.makedirs("clientlogs")
    LOG_FILE = os.path.join("clientlogs", f"{username}_{timestamp}.txt")  
    
def log_message(message):
    """Append message to the log file with a timestamp."""
    global LOG_FILE
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        log.write(f"{timestamp} {message}\n")


def display_message(message):
    message = message.replace("<b>", "**").replace("</b>", "**") 
    message = message.replace("<i>", "*").replace("</i>", "*")
    log_message(message) 
    return message


async def send_message(websocket):
    global send_queue
    while True:
        msg = await send_queue.get()
        if msg.lower() == '/quit':
            await websocket.close()
            message_queue.put("Ending connection.")
            log_message("Ending connection.")
            break
        if current_target:
            payload = json.dumps({"target": current_target, "message": msg})
            await websocket.send(payload)
            message_queue.put(f"To {current_target}: {msg}")
            log_message(f"Sent direct message to {current_target}: {msg}")
        else:
            await websocket.send(msg)
            log_message(f"To everyone: {msg}")  
            message_queue.put(f"{current_target}: {msg}")


async def send_file(file_path):
    """Send a file as binary data."""
    global websocket_ref, current_target
    if not websocket_ref:
        message_queue.put("WebSocket not connected!")
        return
    if not current_target:
        message_queue.put("No target selected for file transfer!")
        return

    try:
        filename = os.path.basename(file_path)
        message_queue.put(f"Sending file: {filename} to {current_target}")
        await websocket_ref.send(json.dumps({"file_transfer": "start", "target": current_target, "filename": filename}))
        with open(file_path, "rb") as file:
            while True:
                chunk = file.read(4096)
                if not chunk:
                    break
                await websocket_ref.send(chunk)

        await websocket_ref.send(json.dumps({"file_transfer": "end", "target": current_target})) 
        message_queue.put(f"File '{filename}' sent successfully to {current_target}.")

    except Exception as e:
        message_queue.put(f"Error sending file: {e}")

async def receive_message(websocket):
    global websocket_ref
    websocket_ref = websocket
    file_buffer = None
    filename = None
    while True:
        try:
            response = await websocket.recv()
            if isinstance(response, str):
                try:
                    data = json.loads(response)
                    if "online_users" in data:
                        message_queue.put({"online_users": data["online_users"]})
                        continue
                    if "direct_message" in data:
                        message_queue.put(display_message(data["direct_message"]))
                        continue

                    if "file_transfer" in data:
                        action = data["file_transfer"]

                        if action == "start":
                            filename = data.get("filename", "unknown")
                            file_buffer = open(f"received_{filename}", "wb")
                            message_queue.put(f"Preparing to receive file: {filename}")

                        elif action == "end":
                            if file_buffer:
                                file_buffer.close()
                                message_queue.put(f"File received: received_{filename}")
                                file_buffer = None
                                filename = None
                        continue
                    
                    message_queue.put(display_message(response))

                except json.JSONDecodeError:
                    message_queue.put(display_message(response))

            elif isinstance(response, bytes):
                if file_buffer:
                    file_buffer.write(response)
                else:
                    message_queue.put("Received unexpected binary data.")

        except websockets.exceptions.ConnectionClosed:
            message_queue.put("Connection closed.")
            log_message("Connection closed.")
            break

async def websocket_client():
    global send_queue, asyncio_loop, websocket_ref
    try:
        send_queue = asyncio.Queue()
        asyncio_loop = asyncio.get_running_loop()
        
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        async with websockets.connect(SERVER_URI, ssl=ssl_context) as websocket:
            websocket_ref = websocket
            message_queue.put("Connected to server.")
            message_queue.put("Enter 'R' to register or 'L' to login: ")
            send_task = asyncio.create_task(send_message(websocket))
            receive_task = asyncio.create_task(receive_message(websocket))
            await asyncio.gather(send_task, receive_task)
    except Exception as e:
        message_queue.put(f"Client error: {e}")

def start_websocket_client():
    asyncio.run(websocket_client())

def start_gui():
    global current_target, current_username
    current_username = None
    root = tk.Tk()
    root.title("SecureTech Industries")

    left_list = tk.Frame(root)
    left_list.pack(side = 'left', fill = 'y', padx = (10,5), pady = (10))
    contacts = tk.Label(left_list, text = "Online Users")
    contacts.pack()
    users = tk.Listbox(left_list, height = (15), width = (20))
    users.pack(fill = 'y', padx = (5), pady = (5))

    def click_user(event):
        global current_target, current_username
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            user = event.widget.get(index)
            if user == current_username:
                message_queue.put("You cannot select yourself.")
                return
            current_target = user
            message_queue.put(f"Chatting with {user} now")
            
    users.bind("<Double-Button-1>", click_user)
    
    chatbox = tk.Frame(root)
    chatbox.pack(side = 'right', fill = 'both', expand = True, padx = (5,10), pady = 10)

    display = tk.Text(chatbox, wrap='word', height=20, width=60)
    display.pack(padx=10, pady=10)
    display.config(state = 'disabled')
    login_status = tk.Label(chatbox, text = "Not logged in", anchor = "w", font = ("Helvetica", 10))
    login_status.pack(padx = 10, pady = (0,10))
    entry = tk.Entry(chatbox, width=50)
    entry.pack(side='left', padx=(10,0), pady=(0,10))
    entry.bind("<Return>", lambda event: click_send())
    def click_send():
        msg = entry.get().strip()
        if msg:
            entry.delete(0, tk.END)
            if asyncio_loop is not None:
                asyncio_loop.call_soon_threadsafe(send_queue.put_nowait, msg)
            if msg.lower() == "/quit":
                entry.config(state='disabled')
                send_button.config(state='disabled')

    def click_send_file():
        """Open file dialog and send the selected file asynchronously."""
        file_path = filedialog.askopenfilename()
        if file_path and asyncio_loop is not None:
            asyncio_loop.create_task(send_file(file_path))
    
    send_button = tk.Button(chatbox, text='Send', command=click_send)
    send_button.pack(side='left', padx=(5,10), pady=(0,10))

    file_button = tk.Button(chatbox, text="Send File", command=click_send_file)
    file_button.pack(side='left', padx=(5,10), pady=(0,10))
    
    emoji_button = tk.Button(chatbox, text = "Emoji", command = lambda: open_emoji(entry))
    emoji_button.pack(side = 'left', padx = (5,10), pady = (0,10))

    def poll():
        global current_username
        while not message_queue.empty():
            msg = message_queue.get()
            if isinstance(msg, dict) and "online_users" in msg:
                users.delete(0, tk.END)
                for user in msg["online_users"]:
                    users.insert(tk.END, user)
            else:
                if isinstance(msg, str) and msg.startswith("Logged in as "):
                    username = msg.replace("Logged in as ", "").strip()
                    current_username = username
                    set_client_log(username)
                    login_status.config(text = f"Logged in as: {username}")
                log_message(str(msg))
                display.config(state = 'normal')
                display.insert(tk.END, str(msg) + "\n")
                display.see(tk.END)
                display.config(state = 'disabled')
        root.after(100, poll)

    poll()
    return root
def open_emoji(entry_widget):
    emojis = [
        "😀", "😃", "😄", "😁", "😆", "🤣", "😊", "😇",
        "😉", "😍", "🤔", "🤗", "🙄", "😏", "😣", "😖",
        "😞", "😡", "❤️", "💔", "🔥", "🎉", "👍", "👎",
        "🚀", "✨", "☕", "🍔", "🍕", "🍎", "⚽"
    ]
    picker_window = tk.Toplevel()
    picker_window.title("Select an Emoji")
    def select_emoji(emoji):
        entry_widget.insert(tk.END, emoji)
        picker_window.destroy()
    rows = 0
    cols = 0
    max_cols = 8 
    for emoji in emojis:
        button = tk.Button(picker_window, text=emoji, font=("Arial", 12),
                           width=2, command=lambda e=emoji: select_emoji(e))
        button.grid(row=rows, column=cols, padx=2, pady=2)
        cols += 1
        if cols >= max_cols:
            cols = 0
            rows += 1
            
if __name__ == "__main__":
    websocket_client_thread = threading.Thread(target=start_websocket_client, daemon=True)
    websocket_client_thread.start()
    gui = start_gui()
    gui.mainloop()
