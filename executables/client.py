import asyncio
import websockets

SERVER_URI = "ws://127.0.0.1:7890"

async def websocket_client():
    async with websockets.connect(SERVER_URI) as websocket:
        while True:
            message = input("Enter message: ")
            if message.lower() == 'end':
                print("Ending connection with server..")
                break
            
            print(f"Sending: {message}")
            await websocket.send(message)

            response = await websocket.recv()
            print(f"Received: {response}")

if __name__ == "__main__":
    asyncio.run(websocket_client())