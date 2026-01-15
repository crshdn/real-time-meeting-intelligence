"""
WebSocket Server for Real-Time Sales Assistant.
Handles IPC between Python backend and Electron frontend.
"""

import asyncio
import json
import logging
from typing import Set, Callable, Optional, Any
from dataclasses import dataclass, asdict, field

import websockets
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)


@dataclass
class TranscriptMessage:
    """Message containing transcript data."""

    type: str = "transcript"
    text: str = ""
    speaker: str = "unknown"
    is_final: bool = False


@dataclass
class SuggestionsMessage:
    """Message containing AI suggestions."""

    type: str = "suggestions"
    items: list = field(default_factory=list)


@dataclass
class StatusMessage:
    """Message containing system status."""

    type: str = "status"
    listening: bool = False
    connected: bool = True
    transcribing: bool = False


@dataclass
class AudioLevelMessage:
    """Message containing audio level for visualization."""

    type: str = "audio_level"
    level: float = 0.0
    has_audio: bool = False


class WebSocketServer:
    """
    WebSocket server for frontend communication.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8765,
    ):
        """
        Initialize WebSocket server.

        Args:
            host: Host to bind to
            port: Port to listen on
        """
        self.host = host
        self.port = port

        self._clients: Set[WebSocketServerProtocol] = set()
        self._message_handler: Optional[Callable[[dict], Any]] = None
        self._server: Optional[websockets.WebSocketServer] = None
        self._is_running = False

    async def start(self) -> None:
        """Start the WebSocket server."""
        if self._is_running:
            logger.warning("WebSocket server already running")
            return

        self._server = await websockets.serve(
            self._handle_connection,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=10,
        )
        self._is_running = True
        logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")

    async def stop(self) -> None:
        """Stop the WebSocket server."""
        if not self._is_running:
            return

        self._is_running = False

        # Close all client connections
        if self._clients:
            await asyncio.gather(
                *[client.close() for client in self._clients],
                return_exceptions=True,
            )
            self._clients.clear()

        # Close server
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

        logger.info("WebSocket server stopped")

    async def _handle_connection(
        self,
        websocket: WebSocketServerProtocol,
    ) -> None:
        """Handle a new WebSocket connection."""
        await self._register(websocket)

        try:
            async for message in websocket:
                await self._handle_message(websocket, message)
        except ConnectionClosed:
            pass
        except Exception as e:
            logger.error(f"Error handling connection: {e}")
        finally:
            await self._unregister(websocket)

    async def _register(self, websocket: WebSocketServerProtocol) -> None:
        """Register a new client connection."""
        self._clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self._clients)}")

        # Send initial status
        try:
            status_msg = StatusMessage(connected=True)
            logger.debug(f"Sending initial status: {status_msg}")
            await self._send_to_client(websocket, status_msg)
            logger.debug("Initial status sent successfully")
        except Exception as e:
            logger.error(f"Error sending initial status: {e}")

    async def _unregister(self, websocket: WebSocketServerProtocol) -> None:
        """Unregister a client connection."""
        self._clients.discard(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self._clients)}")

    async def _handle_message(
        self,
        websocket: WebSocketServerProtocol,
        message: str,
    ) -> None:
        """Handle incoming message from client."""
        try:
            data = json.loads(message)
            logger.debug(f"Received message: {data.get('type', 'unknown')}")

            if self._message_handler:
                response = await self._message_handler(data)
                if response:
                    await self._send_to_client(websocket, response)

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON message: {message[:100]}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def _send_to_client(
        self,
        websocket: WebSocketServerProtocol,
        message: Any,
    ) -> None:
        """Send message to a specific client."""
        try:
            if hasattr(message, "__dataclass_fields__"):
                data = asdict(message)
            elif isinstance(message, dict):
                data = message
            else:
                data = {"data": message}

            await websocket.send(json.dumps(data))
        except ConnectionClosed:
            await self._unregister(websocket)
        except Exception as e:
            logger.error(f"Error sending to client: {e}")

    async def broadcast(self, message: Any) -> None:
        """
        Send message to all connected clients.

        Args:
            message: Message to broadcast (dataclass, dict, or other)
        """
        if not self._clients:
            return

        if hasattr(message, "__dataclass_fields__"):
            data = json.dumps(asdict(message))
        elif isinstance(message, dict):
            data = json.dumps(message)
        else:
            data = json.dumps({"data": message})

        # Send to all clients, handling failures gracefully
        failed_clients = []
        for client in self._clients:
            try:
                await client.send(data)
            except ConnectionClosed:
                failed_clients.append(client)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                failed_clients.append(client)

        # Clean up failed connections
        for client in failed_clients:
            self._clients.discard(client)

    async def broadcast_transcript(
        self,
        text: str,
        speaker: str,
        is_final: bool = False,
    ) -> None:
        """
        Broadcast transcript update to all clients.

        Args:
            text: Transcript text
            speaker: Speaker label
            is_final: Whether this is a final result
        """
        await self.broadcast(
            TranscriptMessage(
                text=text,
                speaker=speaker,
                is_final=is_final,
            )
        )

    async def broadcast_suggestions(self, suggestions: list[str]) -> None:
        """
        Broadcast AI suggestions to all clients.

        Args:
            suggestions: List of suggestion strings
        """
        await self.broadcast(SuggestionsMessage(items=suggestions))

    async def broadcast_status(
        self,
        listening: bool = False,
        connected: bool = True,
        transcribing: bool = False,
    ) -> None:
        """
        Broadcast status update to all clients.

        Args:
            listening: Whether audio capture is active
            connected: Whether backend is connected
            transcribing: Whether transcription is active
        """
        await self.broadcast(
            StatusMessage(
                listening=listening,
                connected=connected,
                transcribing=transcribing,
            )
        )

    async def broadcast_audio_level(self, level: float, has_audio: bool = False) -> None:
        """
        Broadcast audio level for UI visualization.

        Args:
            level: Audio RMS level (0-32767 range for int16)
            has_audio: Whether audio is above silence threshold
        """
        await self.broadcast(
            AudioLevelMessage(
                level=level,
                has_audio=has_audio,
            )
        )

    def on_message(self, handler: Callable[[dict], Any]) -> None:
        """
        Set message handler callback.

        Args:
            handler: Async function called with each message
        """
        self._message_handler = handler

    @property
    def client_count(self) -> int:
        """Number of connected clients."""
        return len(self._clients)

    @property
    def is_running(self) -> bool:
        """Check if server is running."""
        return self._is_running
