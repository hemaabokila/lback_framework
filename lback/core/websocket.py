import websockets
import asyncio
import logging


class WebSocketServer:
    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        self.connected_users = set()

    async def register(self, websocket):
        """Register a new WebSocket connection."""
        self.connected_users.add(websocket)
        logging.info(f"New connection: {websocket.remote_address}. Total connections: {len(self.connected_users)}")

    async def unregister(self, websocket):
        """Unregister a WebSocket connection."""
        self.connected_users.remove(websocket)
        logging.info(f"Connection closed with {websocket.remote_address}. Total connections: {len(self.connected_users)}")

    async def handle_message(self, websocket, message):
        """Process a received message and send a response."""
        try:
            logging.info(f"Received message from {websocket.remote_address}: {message}")
            response = f"Echo: {message}"
            await websocket.send(response)
            logging.info(f"Sent message to {websocket.remote_address}: {response}")
        except Exception as e:
            logging.error(f"Error handling message from {websocket.remote_address}: {e}")

    async def echo(self, websocket):
        """Echo received messages back to the client."""
        async for message in websocket:
            await self.handle_message(websocket, message)

    async def websocket_handler(self, websocket, path):
        """Handle a new WebSocket connection."""
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
        """Start the WebSocket server."""
        server = websockets.serve(self.websocket_handler, self.host, self.port)
        asyncio.get_event_loop().run_until_complete(server)
        logging.info(f"WebSocket server is running on ws://{self.host}:{self.port}...")
        asyncio.get_event_loop().run_forever()
