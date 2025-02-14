import websockets
import asyncio

PORT = 7890

print("testing on port " + str(PORT))
connected_clients = set()

async def messaging(websocket): 
    print("A client connected")
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            print(f"Message received: {message}")
            for client in connected_clients:
                if client != websocket:
                    await client.send(message)
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
        server = await websockets.serve(messaging, "0.0.0.0", PORT)
        print(f"WebSocket server started on ws://0.0.0.0:{PORT}")
        await server.wait_closed()
    except Exception as e:
        print(f"Fatal server error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
