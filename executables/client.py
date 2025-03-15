import asyncio
import websockets
import ssl
import tkinter as tk
import threading
import queue

SERVER_URI = "wss://192.168.68.68:7890"

message_queue = queue.Queue()
send_queue = None
asyncio_loop = None

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
    
async def receive_message(websocket):
    while True:
        try:
            response = await websocket.recv()
        except websockets.exceptions.ConnectionClosed:
            message_queue.put("Connection closed.")
            break
        formatted_response = display_message(response)
        message_queue.put(f"Receive: {formatted_response}")
        
async def websocket_client():
    try:
        global send_queue, asyncio_loop
        send_queue = asyncio.Queue()
        asyncio_loop = asyncio.get_running_loop()
        
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        async with websockets.connect(SERVER_URI, ssl=ssl_context) as websocket:
            message_queue.put("Connected to server.")
            send_task = asyncio.create_task(send_message(websocket))
            receive_task = asyncio.create_task(receive_message(websocket))
            await asyncio.gather(send_task, receive_task)
    except websockets.exceptions.ConnectionClosedError:
        message_queue.put("Connection was closed by the server.")
    except Exception as e:
        message_queue.put(f"Client encountered an error: {e}")
        
def start_websocket_client():
    asyncio.run(websocket_client())

def start_gui():
    root = tk.Tk()
    root.title("SecureTech Industries")
    display = tk.Text(root, wrap = 'word', height = 20, width = 60)
    display.pack(padx = 10, pady = 10)
    entry = tk.Entry(root, width = 50)
    entry.pack(side = 'left', padx = (10,0), pady = (0,10))
    
    def click_send():
        msg = entry.get().strip()
        if msg:
            entry.delete(0,tk.END)
            if asyncio_loop is not None:
                asyncio_loop.call_soon_threadsafe(send_queue.put_nowait, msg)
            if msg.lower() == "end":
                entry.config(state='disabled')
                send_button.config(state='disabled')
                
    send_button = tk.Button(root, text = 'Send', command = click_send)
    send_button.pack(side = 'left', padx = (5,10), pady = (0,10))
        
    def poll():
        while not message_queue.empty():
            msg = message_queue.get()
            display.insert(tk.END, msg + "\n")
            display.see(tk.END)
        root.after(100, poll)
        
    poll()
    return root
    
    
if __name__ == "__main__":
    websocket_client_thread = threading.Thread(target=start_websocket_client, daemon = True)
    websocket_client_thread.start()
    gui = start_gui()
    gui.mainloop()
