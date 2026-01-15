"""
Main Entry Point for Real-Time Sales Assistant Backend.
Orchestrates audio capture, transcription, and suggestion generation.
"""

import asyncio
import logging
import os
import signal
import sys
import time
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

from audio_capture import AudioCapture
from transcription import DeepgramTranscriber, TranscriptResult
from context_manager import ConversationBuffer
from llm_generator import SuggestionGenerator
from websocket_server import WebSocketServer

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Configure logging - temporarily enable DEBUG
log_level = logging.DEBUG  # TODO: change back to: logging.DEBUG if os.environ.get("DEBUG") == "1" else logging.INFO
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Suppress noisy websockets library logs (invalid HTTP requests, handshake errors, etc.)
logging.getLogger("websockets.server").setLevel(logging.CRITICAL)
logging.getLogger("websockets.protocol").setLevel(logging.CRITICAL)
logging.getLogger("websockets.asyncio.server").setLevel(logging.CRITICAL)


class SalesAssistant:
    """
    Main application class that orchestrates all components.
    """

    def __init__(self):
        """Initialize the sales assistant."""
        self.audio_capture = AudioCapture(
            sample_rate=16000,
            channels=1,
            blocksize=4000,  # 250ms chunks
        )
        self.transcriber = DeepgramTranscriber(
            sample_rate=16000,
            channels=1,
            enable_diarization=True,
        )
        self.context_buffer = ConversationBuffer(
            max_duration_seconds=180,
            suggestion_cooldown=5.0,
        )
        self.suggestion_generator = SuggestionGenerator()
        self.websocket_server = WebSocketServer(
            host="localhost",
            port=int(os.environ.get("WEBSOCKET_PORT", 8765)),
        )

        self._is_running = False
        self._is_listening = False
        self._audio_task: asyncio.Task | None = None
        self._generation_lock = asyncio.Lock()

    async def start(self) -> None:
        """Start the sales assistant."""
        logger.info("Starting Sales Assistant...")

        # Set up message handler
        self.websocket_server.on_message(self._handle_client_message)

        # Start WebSocket server
        await self.websocket_server.start()

        self._is_running = True
        logger.info("Sales Assistant ready. Waiting for client connections...")

        # Keep running until stopped
        while self._is_running:
            await asyncio.sleep(1)

    async def stop(self) -> None:
        """Stop the sales assistant."""
        logger.info("Stopping Sales Assistant...")

        self._is_running = False
        await self._stop_listening()
        await self.websocket_server.stop()

        logger.info("Sales Assistant stopped")

    async def _start_listening(self) -> None:
        """Start audio capture and transcription."""
        if self._is_listening:
            logger.warning("Already listening")
            return

        logger.info("Starting audio capture and transcription...")

        try:
            # Start audio capture
            self.audio_capture.start()

            # Connect to Deepgram
            await self.transcriber.connect(self._on_transcript)

            # Start audio streaming task
            self._audio_task = asyncio.create_task(self._stream_audio())

            self._is_listening = True

            # Notify clients
            await self.websocket_server.broadcast_status(
                listening=True,
                connected=True,
                transcribing=True,
            )

            logger.info("Now listening for audio")

        except Exception as e:
            logger.error(f"Failed to start listening: {e}")
            # Reset state on failure
            self._is_listening = False
            self.audio_capture.stop()
            await self.transcriber.disconnect()
            raise

    async def _stop_listening(self) -> None:
        """Stop audio capture and transcription."""
        if not self._is_listening:
            return

        logger.info("Stopping audio capture and transcription...")

        self._is_listening = False

        # Cancel audio task
        if self._audio_task:
            self._audio_task.cancel()
            try:
                await self._audio_task
            except asyncio.CancelledError:
                pass
            self._audio_task = None

        # Stop components
        self.audio_capture.stop()
        await self.transcriber.disconnect()

        # Clear conversation buffer
        self.context_buffer.clear()

        # Notify clients
        await self.websocket_server.broadcast_status(
            listening=False,
            connected=True,
            transcribing=False,
        )

        logger.info("Stopped listening")

    async def _stream_audio(self) -> None:
        """Task to stream audio from capture to transcriber."""
        logger.debug("Audio streaming task started")

        # Audio level tracking for debugging
        last_level_log = time.time()
        level_log_interval = 2.0  # Log audio level every 2 seconds
        recent_levels = []

        try:
            while self._is_listening:
                # Get audio chunk
                audio_data = await self.audio_capture.get_chunk_async(timeout=0.5)
                if audio_data is None:
                    continue

                # Calculate audio level for debugging
                rms = np.sqrt(np.mean(audio_data.astype(np.float64) ** 2))
                recent_levels.append(rms)

                # Log and broadcast audio level periodically
                now = time.time()
                if now - last_level_log >= level_log_interval:
                    avg_level = float(np.mean(recent_levels)) if recent_levels else 0.0
                    peak_level = float(np.max(recent_levels)) if recent_levels else 0.0
                    has_audio = avg_level > 100

                    if has_audio:
                        logger.info(f"Audio level: avg={avg_level:.0f}, peak={peak_level:.0f} - AUDIO DETECTED")
                    else:
                        logger.debug(f"Audio level: avg={avg_level:.0f}, peak={peak_level:.0f} - silence")

                    # Broadcast to frontend for visualization (in try/except to not crash the loop)
                    try:
                        await self.websocket_server.broadcast_audio_level(avg_level, has_audio)
                    except Exception as e:
                        logger.warning(f"Failed to broadcast audio level: {e}")

                    recent_levels = []
                    last_level_log = now

                # Send to Deepgram
                await self.transcriber.send_audio(audio_data.tobytes())

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in audio streaming: {e}")

        logger.debug("Audio streaming task ended")

    def _on_transcript(self, result: TranscriptResult) -> None:
        """
        Callback for transcript results from Deepgram.
        Runs in the transcriber's context, so we schedule async work.
        """
        # Add to conversation buffer
        self.context_buffer.add_transcript(
            text=result.text,
            speaker=result.speaker,
            is_final=result.is_final,
        )

        # Schedule async broadcast and suggestion generation
        asyncio.create_task(self._process_transcript(result))

    async def _process_transcript(self, result: TranscriptResult) -> None:
        """Process transcript result and potentially generate suggestions."""
        # Map speaker ID to label
        speaker_label = "prospect" if result.speaker == 0 else "salesperson"

        # Broadcast transcript to clients
        await self.websocket_server.broadcast_transcript(
            text=result.text,
            speaker=speaker_label,
            is_final=result.is_final,
        )

        # Check if we should generate suggestions
        if result.is_final and self.context_buffer.should_trigger_ai():
            await self._generate_suggestions()

    async def _generate_suggestions(self) -> None:
        """Generate and broadcast AI suggestions."""
        # Use lock to prevent concurrent generation
        if self._generation_lock.locked():
            return

        async with self._generation_lock:
            last_statement = self.context_buffer.get_last_prospect_statement()
            if not last_statement:
                return

            context = self.context_buffer.get_context_string(last_n=10)

            logger.info(f"Generating suggestions for: {last_statement[:50]}...")

            # Run generation in thread pool to not block
            loop = asyncio.get_event_loop()
            suggestions = await loop.run_in_executor(
                None,
                self.suggestion_generator.generate_sync,
                context,
                last_statement,
            )

            if suggestions:
                self.context_buffer.mark_suggestion_sent()
                await self.websocket_server.broadcast_suggestions(suggestions)
                logger.info(f"Broadcast {len(suggestions)} suggestions")

    async def _handle_client_message(self, data: dict) -> dict | None:
        """
        Handle messages from frontend clients.

        Args:
            data: Message data from client

        Returns:
            Optional response message
        """
        msg_type = data.get("type")

        if msg_type == "start_listening":
            try:
                await self._start_listening()
                return {"type": "ack", "success": True}
            except Exception as e:
                return {"type": "error", "message": str(e)}

        elif msg_type == "stop_listening":
            await self._stop_listening()
            return {"type": "ack", "success": True}

        elif msg_type == "get_status":
            return {
                "type": "status",
                "listening": self._is_listening,
                "connected": True,
                "transcribing": self._is_listening and self.transcriber.is_connected,
            }

        elif msg_type == "clear_buffer":
            self.context_buffer.clear()
            return {"type": "ack", "success": True}

        else:
            logger.warning(f"Unknown message type: {msg_type}")
            return None


async def main():
    """Main entry point."""
    assistant = SalesAssistant()

    # Set up signal handlers for graceful shutdown
    loop = asyncio.get_event_loop()

    def signal_handler():
        logger.info("Received shutdown signal")
        asyncio.create_task(assistant.stop())

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    try:
        await assistant.start()
    except KeyboardInterrupt:
        pass
    finally:
        await assistant.stop()


if __name__ == "__main__":
    asyncio.run(main())
