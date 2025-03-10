import websockets
import asyncio
import ssl

PORT = 7890

connected_clients = set()

def format_message(message):
    message = message.replace("**", "<b>").replace("**", "</b>")
    message = message.replace("*", "<i>").replace("*", "</i>")
    return message

async def messaging(websocket): 
    print("A client connected")
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            print(f"Message received: {message}")
            formatted_message = format_message(message)
            for client in connected_clients:
                if client != websocket:
                    await client.send(formatted_message)
    except websockets.exceptions.ConnectionClosedError:
        print("Client disconnected unexpectedly.")
    except Exception as e:
        print(f"Server encountered an error: {e}")
    finally:
        print("Client disconnecting...")
        connected_clients.remove(websocket)
        await websocket.close()
        
async def main():
    try:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(certfile="./executables/certificate.pem", keyfile="./executables/privateKey.pem")
        server = await websockets.serve(messaging, "0.0.0.0", PORT, ssl=ssl_context)
        print(f"WebSocket server started on wss://0.0.0.0:{PORT}")
        await server.wait_closed()
    except Exception as e:
        print(f"Fatal server error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
