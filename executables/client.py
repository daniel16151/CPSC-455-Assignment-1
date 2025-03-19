import asyncio
import websockets
import ssl
import tkinter as tk
import threading
import queue
from tkinter import filedialog
import os

SERVER_URI = "wss://192.168.68.68:7890"

message_queue = queue.Queue()
send_queue = None
asyncio_loop = None
websocket_ref = None  

def display_message(message):
    message = message.replace("<b>", "**").replace("</b>", "**") 
    message = message.replace("<i>", "*").replace("</i>", "*")
    return message

async def send_message(websocket):
    global send_queue
    while True:
        msg = await send_queue.get()
        if msg.lower() == 'end':
            await websocket.close()
            message_queue.put("Ending connection.")
            break
        await websocket.send(msg) 
        message_queue.put(f"Sent: {msg}")

async def send_file(file_path):
    """Send a file as binary data."""
    global websocket_ref
    if not websocket_ref:
        message_queue.put("WebSocket not connected!")
        return

    try:
        filename = os.path.basename(file_path)
        message_queue.put(f"Sending file: {filename}")

        
        await websocket_ref.send(f"FILE:{filename}")

        
        with open(file_path, "rb") as file:
            while True:
                chunk = file.read(4096)
                if not chunk:
                    break
                await websocket_ref.send(chunk)

        await websocket_ref.send("FILE_END")  
        message_queue.put(f"File {filename} sent successfully.")

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
                if response.startswith("FILE:"):
                    filename = response.split(":", 1)[1]
                    file_buffer = open(f"received_{filename}", "wb")
                    message_queue.put(f"Receiving file: {filename}")
                elif response == "FILE_END" and file_buffer:
                    file_buffer.close()
                    message_queue.put(f"File received: received_{filename}")
                    filename, file_buffer = None, None
                else:
                    message_queue.put(f"Receive: {display_message(response)}")

            elif isinstance(response, bytes) and file_buffer:  
                file_buffer.write(response)

        except websockets.exceptions.ConnectionClosed:
            message_queue.put("Connection closed.")
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
            send_task = asyncio.create_task(send_message(websocket))
            receive_task = asyncio.create_task(receive_message(websocket))
            await asyncio.gather(send_task, receive_task)
    except Exception as e:
        message_queue.put(f"Client error: {e}")

def start_websocket_client():
    asyncio.run(websocket_client())

def start_gui():
    root = tk.Tk()
    root.title("SecureTech Industries")
    display = tk.Text(root, wrap='word', height=20, width=60)
    display.pack(padx=10, pady=10)
    entry = tk.Entry(root, width=50)
    entry.pack(side='left', padx=(10,0), pady=(0,10))

    def click_send():
        msg = entry.get().strip()
        if msg:
            entry.delete(0, tk.END)
            if asyncio_loop is not None:
                asyncio_loop.call_soon_threadsafe(send_queue.put_nowait, msg)
            if msg.lower() == "end":
                entry.config(state='disabled')
                send_button.config(state='disabled')

    def click_send_file():
        """Open file dialog and send the selected file asynchronously."""
        file_path = filedialog.askopenfilename()
        if file_path and asyncio_loop is not None:
            asyncio_loop.create_task(send_file(file_path))

    send_button = tk.Button(root, text='Send', command=click_send)
    send_button.pack(side='left', padx=(5,10), pady=(0,10))

    file_button = tk.Button(root, text="Send File", command=click_send_file)
    file_button.pack(side='left', padx=(5,10), pady=(0,10))

    def poll():
        while not message_queue.empty():
            msg = message_queue.get()
            display.insert(tk.END, msg + "\n")
            display.see(tk.END)
        root.after(100, poll)

    poll()
    return root

if __name__ == "__main__":
    websocket_client_thread = threading.Thread(target=start_websocket_client, daemon=True)
    websocket_client_thread.start()
    gui = start_gui()
    gui.mainloop()
