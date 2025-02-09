import asyncio
import websockets

SERVER_URI = "ws://localhost:7890"

async def websocket_client():
    async with websockets.connect(SERVER_URI) as websocket:
        message = "Hello, WebSocket Server!"
        print(f"Sending: {message}")
        await websocket.send(message)

        response = await websocket.recv()
        print(f"Received: {response}")

if __name__ == "__main__":
    asyncio.run(websocket_client())