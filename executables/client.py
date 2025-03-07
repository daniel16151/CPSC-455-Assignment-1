import asyncio
import websockets
import ssl

SERVER_URI = "wss://10.67.33.35:7890"
        
async def websocket_client():
    try:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        async with websockets.connect(SERVER_URI, ssl=ssl_context) as websocket:
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
