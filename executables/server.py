import websockets
import asyncio

PORT = 7890

print("testing on port " + str(PORT))

async def echo(websocket, _):
    print("A client connected")
    try:
        async for message in websocket:
            print(f"Message received: {message}")
            await websocket.send(f"Pong: {message}")
    except websockets.exceptions.ConnectionClosedError:
        print("Client disconnected unexpectedly.")
    except Exception as e:
        print(f"Server encountered an error: {e}")  # Log the error
    finally:
        print("Closing connection...")
        
        
async def main():
    try:
        server = await websockets.serve(echo, "localhost", PORT)
        print(f"WebSocket server started on ws://localhost:{PORT}")
        await server.wait_closed()
    except Exception as e:
        print(f"Fatal server error: {e}")

if __name__ == "__main__":
    asyncio.run(main())