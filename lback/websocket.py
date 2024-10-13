import websockets
import asyncio
import logging

logging.basicConfig(level=logging.INFO)

class WebSocketServer:
    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        self.connected_users = set()

    async def register(self, websocket):
        self.connected_users.add(websocket)
        logging.info(f"New connection: {websocket.remote_address}")

    async def unregister(self, websocket):
        self.connected_users.remove(websocket)
        logging.info(f"Connection closed with {websocket.remote_address}")

    async def echo(self, websocket):
        async for message in websocket:
            logging.info(f"Received message: {message}")
            response = f"Echo: {message}"
            await websocket.send(response)
            logging.info(f"Sent message: {response}")

    async def websocket_handler(self, websocket, path):
        await self.register(websocket)
        try:
            await self.echo(websocket)
        except websockets.ConnectionClosed as e:
            logging.warning(f"Connection closed: {e}")
        except Exception as e:
            logging.error(f"Error: {e}")
        finally:
            await self.unregister(websocket)

    def start(self):
        server = websockets.serve(self.websocket_handler, self.host, self.port)
        asyncio.get_event_loop().run_until_complete(server)
        logging.info(f"WebSocket server is running on ws://{self.host}:{self.port}...")
        asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    ws_server = WebSocketServer()
    ws_server.start()
