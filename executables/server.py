import websockets
import asyncio
import ssl

PORT = 7890
connected_clients = set()

import datetime

LOG_FILE = "server_chat_log.txt"

def log_message(message):
    """Append message to the log file with a timestamp."""
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        log.write(f"{timestamp} {message}\n")


async def messaging(websocket): 
    print("A client connected")
    log_message("A client connected")
    connected_clients.add(websocket)
    
    try:
        async for message in websocket:
            if isinstance(message, str):  
                if message.startswith("FILE:"):
                    filename = message.split(":", 1)[1]
                    file_buffer = open(f"received_{filename}", "wb")
                    print(f"Receiving file: {filename}")
                    log_message(f"Receiving file: {filename}")

                    for client in connected_clients:
                        if client != websocket:
                            await client.send(f"FILE:{filename}")

                elif message == "FILE_END" and file_buffer:
                    file_buffer.close()
                    print(f"File received: {filename}")
                    log_message(f"File received: {filename}")

                    for client in connected_clients:
                        if client != websocket:
                            await client.send("FILE_END")
                    file_buffer = None

                else:
                    print(f"Received: {message}")
                    log_message(f"Received: {message}")

                    for client in connected_clients:
                        if client != websocket:
                            await client.send(message)

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
        await websocket.close()

async def main():
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(certfile="./executables/certificate.pem", keyfile="./executables/privateKey.pem")
    server = await websockets.serve(messaging, "0.0.0.0", PORT, ssl=ssl_context)
    print(f"WebSocket server started on wss://0.0.0.0:{PORT}")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
