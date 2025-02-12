import asyncio
import websockets

SERVER_URI = "ws://127.0.0.1:7890"

async def websocket_client():
    try:
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
    except websockets.exceptions.ConnectionClosedError:
        print("Connection was closed by the server.")
    except Exception as e:
        print(f"Client encountered an error: {e}")

if __name__ == "__main__":
    asyncio.run(websocket_client())
