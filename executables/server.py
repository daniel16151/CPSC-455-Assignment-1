import websockets
import asyncio
import ssl
import json
import hashlib
import os
import datetime

PORT = 443
connected_clients = set()
client_to_user = {}
client_state = {} 
client_temp = {}

LOG_FILE = "server_chat_log.txt"

user_file = "user.json"

def log_message(message):
    """Append message to the log file with a timestamp."""
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        log.write(f"{timestamp} {message}\n")

def load_user():
    if os.path.exists(user_file):
        with open(user_file, "r", encoding="utf-8") as f:
            user_data = json.load(f)
            return user_data
    print("No user data found.")
    return {}

def save_user(user):
    with open(user_file, "w", encoding="utf-8") as f:
        json.dump(user, f)
        
def hash_pass(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

user = load_user()

def sanitize(message: str) -> str:
    return message.strip().replace("\n","").replace("<","").replace(">","").replace("(","").replace(")","")

async def messaging(websocket): 
    print("A client connected")
    log_message("A client connected")
    connected_clients.add(websocket)
    
    try:
        async for message in websocket:
            if isinstance(message, str):
                if websocket in client_state:
                    state = client_state[websocket]
                    if state == "register_user":
                        username = message.strip()
                        client_temp[websocket] = {"action": "register", "username": username}
                        client_state[websocket] = "register_pass"
                        await websocket.send("Enter password:")
                        continue
                    elif state == "register_pass":
                        password = message.strip()
                        special_characters = "~`!@#$%^&*-_=+}{[]|,.?"
                        forbidden_characters = "([\/:;])&'`"
                        if len(password) < 8:
                            await websocket.send("Error: Password must be at least 8 characters long. Enter a new password:")
                            continue
                        if len(password) > 20:
                            await websocket.send("Error: Password must be at most 20 characters long. Enter a new password:")
                            continue
                        if not any(l.isupper() for l in password):
                            await websocket.send("Error: Password must include at least 1 uppercase character. Enter a new password:")
                            continue
                        if not any(l.islower() for l in password):
                            await websocket.send("Error: Password must include at least 1 lowercase character. Enter a new password:")
                            continue
                        if not any(l.isdigit() for l in password):
                            await websocket.send("Error: Password must include at least 1 digit. Enter a new password:")
                            continue
                        if not any(l in special_characters for l in password):
                            await websocket.send("Error: Password must include at least 1 special character. Enter a new password:")
                            continue
                        if not any(l in special_characters for l in password):
                            await websocket.send("Error: Password must include at least 1 special character. Enter a new password:")
                            continue
                        if any(l in forbidden_characters for l in password):
                            await websocket.send("Error: Password must not include any forbidden characters ([\"/:;])&'`: . Enter a new password:")
                            continue
                        data = client_temp.get(websocket, {})
                        username = data.get("username")
                        if username is None:
                            await websocket.send("Error: Blank user.")
                        elif username in user:
                            await websocket.send("Error: User already taken.")
                        else:
                            user[username] = hash_pass(password)
                            save_user(user)
                            await websocket.send("Registration Successful")
                            log_message(f"User registered: {username}")
                        client_state.pop(websocket, None)
                        client_temp.pop(websocket, None)
                        continue
                    elif state == "login_user":
                        username = message.strip()
                        client_temp[websocket] = {"action": "login", "username": username}
                        client_state[websocket] = "login_pass"
                        await websocket.send("Enter password:")
                        continue
                    elif state == "login_pass":
                        password = message.strip()
                        data = client_temp.get(websocket, {})
                        username = data.get("username")
                        if username is None:
                            await websocket.send("Error: Blank User.")
                        elif username not in user:
                            await websocket.send("Error: User or Pass not found.")
                        elif user[username] != hash_pass(password):
                            await websocket.send("Error: User or Pass not found.")
                        else:
                            client_to_user[websocket] = username
                            await websocket.send(f"Logged in as {username}")
                            log_message(f"User logged in: {username}")
                        client_state.pop(websocket, None)
                        client_temp.pop(websocket, None)
                        continue
                    
                if websocket not in client_to_user:
                    if message.strip().upper() == "R":
                        client_state[websocket] = "register_user"
                        await websocket.send("Enter username:")
                        continue
                    elif message.strip().upper() == "L":
                        client_state[websocket] = "login_user"
                        await websocket.send("Enter username:")
                        continue
                    else:
                        await websocket.send("Error: You must log in or register first. Send 'L' for login or 'R' for registration.")
                        continue
                    
                if message.startswith("FILE:"):
                    filename = message.split(":", 1)[1]
                    file_buffer = open(f"received_{filename}", "wb")
                    print(f"Receiving file: {filename}")
                    log_message(f"Receiving file: {filename}")
                    for client in connected_clients:
                        if client != websocket:
                            await client.send(f"FILE:{filename}")
                    continue

                elif message == "FILE_END" and file_buffer:
                    file_buffer.close()
                    print(f"File received: {filename}")
                    log_message(f"File received: {filename}")
                    for client in connected_clients:
                        if client != websocket:
                            await client.send("FILE_END")
                    file_buffer = None
                    continue

                data = json.loads(message)
                if isinstance(data, dict) and "target" in data:
                    target_user = data["target"]
                    direct_message = data.get("message", "")
                    sender = client_to_user.get(websocket, "Unknown")
                    target_socket = None
                    for client, username in client_to_user.items():
                        if username == target_user:
                            target_socket = client
                            break
                        if target_socket is None:
                            await websocket.send(json.dumps({"Error: Targeted User is offline."}))
                        else:
                            await target_socket.send(json.dumps({"direct_message": f"{sender}: {direct_message}"}))
                            await websocket.send(json.dumps({"info": f"Direct message sent to {target_user}"}))
                            continue

                sender = client_to_user.get(websocket, "Unknown")
                broadcast_message = f"{sender}: {message}"
                print(f"Received: {broadcast_message}")
                log_message(f"Received: {broadcast_message}")
                for client in connected_clients:
                    if client != websocket:
                        await client.send(broadcast_message)
            
            elif isinstance(message, bytes) and file_buffer:
                file_buffer.write(message)
                for client in connected_clients:
                    if client != websocket:
                        await client.send(message)

    except websockets.exceptions.ConnectionClosedError:
        print("Client disconnected unexpectedly.")
        log_message("Client disconnected unexpectedly.")
    finally:
        connected_clients.remove(websocket)
        if websocket in client_to_user:
            username = client_to_user.pop(websocket)
            log_message(f"User logged out: {username}")
        client_state.pop(websocket, None)
        client_temp.pop(websocket, None)
        await websocket.close()

async def main():
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(certfile="./executables/certificate.pem", keyfile="./executables/privateKey.pem")
    server = await websockets.serve(messaging, "0.0.0.0", PORT, ssl=ssl_context)
    print(f"WebSocket server started on wss://0.0.0.0:{PORT}")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
