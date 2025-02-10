import websockets
import asyncio

PORT = 7890

print("testing on port " + str(PORT))

async def echo(websocket):
    print("A client connected")
    try:
        async for message in websocket:
            print(f"Message received: {message}")
            await websocket.send(f"Pong: {message}")
    except websockets.exceptions.ConnectionClosedError:
        print("Client disconnected unexpectedly.")
    except Exception as e:
        print(f"Server encountered an error: {e}")
    finally:
        print("Client disconnecting...")
        
        
async def main():
    try:
        server = await websockets.serve(echo, "127.0.0.1", PORT)
        print(f"WebSocket server started on ws://127.0.0.1:{PORT}")
        await server.wait_closed()
    except Exception as e:
        print(f"Fatal server error: {e}")

if __name__ == "__main__":
    asyncio.run(main())