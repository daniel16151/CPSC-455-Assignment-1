import asyncio
import websockets

async def hello():
    async with websockets.connect("ws://localhost:8765") as websocket:
        await websocket.send("Hello, world!")
        message = await websocket.recv()
        print(f"Received: {message}")

asyncio.run(hello())