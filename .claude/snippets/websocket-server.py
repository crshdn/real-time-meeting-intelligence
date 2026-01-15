# WebSocket Server Snippet
# IPC between Python backend and Electron frontend

import asyncio
import websockets
import json
from typing import Set, Callable
from dataclasses import dataclass, asdict

@dataclass
class TranscriptMessage:
    type: str = "transcript"
    text: str = ""
    speaker: str = "unknown"
    is_final: bool = False

@dataclass
class SuggestionsMessage:
    type: str = "suggestions"
    items: list = None

    def __post_init__(self):
        if self.items is None:
            self.items = []

@dataclass
class StatusMessage:
    type: str = "status"
    listening: bool = False
    connected: bool = True


class WebSocketServer:
    """WebSocket server for frontend communication."""

    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.message_handler: Callable = None

    async def register(self, websocket):
        """Register a new client connection."""
        self.clients.add(websocket)
        print(f"Client connected. Total clients: {len(self.clients)}")
        # Send initial status
        await self.send_to_client(websocket, StatusMessage(connected=True))

    async def unregister(self, websocket):
        """Unregister a client connection."""
        self.clients.discard(websocket)
        print(f"Client disconnected. Total clients: {len(self.clients)}")

    async def send_to_client(self, websocket, message):
        """Send message to a specific client."""
        try:
            if hasattr(message, '__dataclass_fields__'):
                data = asdict(message)
            else:
                data = message
            await websocket.send(json.dumps(data))
        except websockets.exceptions.ConnectionClosed:
            await self.unregister(websocket)

    async def broadcast(self, message):
        """Send message to all connected clients."""
        if self.clients:
            data = asdict(message) if hasattr(message, '__dataclass_fields__') else message
            await asyncio.gather(
                *[client.send(json.dumps(data)) for client in self.clients],
                return_exceptions=True
            )

    async def handler(self, websocket, path):
        """Handle WebSocket connection."""
        await self.register(websocket)
        try:
            async for message in websocket:
                data = json.loads(message)
                print(f"Received: {data}")

                if self.message_handler:
                    response = await self.message_handler(data)
                    if response:
                        await self.send_to_client(websocket, response)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)

    def on_message(self, handler: Callable):
        """Set message handler callback."""
        self.message_handler = handler

    async def start(self):
        """Start the WebSocket server."""
        server = await websockets.serve(self.handler, self.host, self.port)
        print(f"WebSocket server started on ws://{self.host}:{self.port}")
        await server.wait_closed()


# Message handler example
async def handle_message(data: dict):
    """Example message handler."""
    msg_type = data.get("type")

    if msg_type == "start_listening":
        print("Starting audio capture...")
        return StatusMessage(listening=True)

    elif msg_type == "stop_listening":
        print("Stopping audio capture...")
        return StatusMessage(listening=False)

    elif msg_type == "update_playbook":
        playbook = data.get("playbook", {})
        print(f"Updating playbook: {playbook.keys()}")
        return {"type": "ack", "success": True}

    return None


# Usage example:
if __name__ == "__main__":
    server = WebSocketServer(port=8765)
    server.on_message(handle_message)

    async def demo():
        # Start server
        server_task = asyncio.create_task(server.start())

        # Simulate sending messages after delay
        await asyncio.sleep(2)
        await server.broadcast(TranscriptMessage(
            text="Hello, I'm interested in your product.",
            speaker="prospect",
            is_final=True
        ))

        await asyncio.sleep(1)
        await server.broadcast(SuggestionsMessage(
            items=[
                "Great to hear! What specific challenges are you facing?",
                "Thanks for your interest! Can you tell me about your current setup?",
            ]
        ))

        await server_task

    asyncio.run(demo())
