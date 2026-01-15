"""
Deepgram Transcription Module for Real-Time Sales Assistant.
Handles real-time speech-to-text via WebSocket streaming.
"""

import asyncio
import json
import logging
import os
from typing import Optional, Callable, Any
from dataclasses import dataclass

import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

logger = logging.getLogger(__name__)


@dataclass
class TranscriptResult:
    """Represents a transcription result from Deepgram."""

    text: str
    speaker: int
    is_final: bool
    confidence: float = 0.0
    start_time: float = 0.0
    end_time: float = 0.0


class DeepgramTranscriber:
    """
    Real-time transcription using Deepgram's streaming WebSocket API.
    """

    DEEPGRAM_URL = "wss://api.deepgram.com/v1/listen"

    def __init__(
        self,
        api_key: Optional[str] = None,
        sample_rate: int = 16000,
        channels: int = 1,
        language: str = "en",
        model: str = "nova-2",
        enable_diarization: bool = True,
    ):
        """
        Initialize Deepgram transcriber.

        Args:
            api_key: Deepgram API key (or from DEEPGRAM_API_KEY env var)
            sample_rate: Audio sample rate in Hz
            channels: Number of audio channels
            language: Language code (e.g., 'en', 'es')
            model: Deepgram model to use
            enable_diarization: Enable speaker diarization
        """
        self.api_key = api_key or os.environ.get("DEEPGRAM_API_KEY")
        if not self.api_key:
            raise ValueError("Deepgram API key required")

        self.sample_rate = sample_rate
        self.channels = channels
        self.language = language
        self.model = model
        self.enable_diarization = enable_diarization

        self._websocket: Optional[websockets.WebSocketClientProtocol] = None
        self._is_connected = False
        self._transcript_callback: Optional[Callable[[TranscriptResult], Any]] = None
        self._send_task: Optional[asyncio.Task] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._audio_queue: Optional[asyncio.Queue] = None

    def _build_url(self) -> str:
        """Build Deepgram WebSocket URL with parameters."""
        params = [
            f"encoding=linear16",
            f"sample_rate={self.sample_rate}",
            f"channels={self.channels}",
            f"language={self.language}",
            f"model={self.model}",
            f"punctuate=true",
            f"interim_results=true",
            f"endpointing=300",
            f"vad_events=true",
        ]
        if self.enable_diarization:
            params.append("diarize=true")

        return f"{self.DEEPGRAM_URL}?{'&'.join(params)}"

    async def connect(
        self,
        transcript_callback: Callable[[TranscriptResult], Any],
    ) -> None:
        """
        Connect to Deepgram WebSocket.

        Args:
            transcript_callback: Called with each transcript result
        """
        if self._is_connected:
            logger.warning("Already connected to Deepgram")
            return

        self._transcript_callback = transcript_callback
        self._audio_queue = asyncio.Queue()

        url = self._build_url()
        headers = {"Authorization": f"Token {self.api_key}"}

        try:
            self._websocket = await websockets.connect(
                url,
                additional_headers=headers,
                ping_interval=20,
                ping_timeout=10,
            )
            self._is_connected = True
            logger.info("Connected to Deepgram")

            # Start send and receive tasks
            self._send_task = asyncio.create_task(self._send_audio())
            self._receive_task = asyncio.create_task(self._receive_transcripts())

        except Exception as e:
            logger.error(f"Failed to connect to Deepgram: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from Deepgram WebSocket."""
        if not self._is_connected:
            return

        self._is_connected = False

        # Cancel tasks
        if self._send_task:
            self._send_task.cancel()
            try:
                await self._send_task
            except asyncio.CancelledError:
                pass

        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

        # Close WebSocket
        if self._websocket:
            try:
                await self._websocket.close()
            except Exception:
                pass
            self._websocket = None

        logger.info("Disconnected from Deepgram")

    async def send_audio(self, audio_data: bytes) -> None:
        """
        Queue audio data for sending to Deepgram.

        Args:
            audio_data: Raw audio bytes (int16 PCM)
        """
        if self._audio_queue and self._is_connected:
            await self._audio_queue.put(audio_data)

    async def _send_audio(self) -> None:
        """Task to send queued audio to Deepgram."""
        try:
            while self._is_connected and self._websocket:
                try:
                    # Get audio from queue with timeout
                    audio_data = await asyncio.wait_for(
                        self._audio_queue.get(),
                        timeout=1.0,
                    )
                    await self._websocket.send(audio_data)
                except asyncio.TimeoutError:
                    continue
                except ConnectionClosed:
                    logger.warning("Deepgram connection closed while sending")
                    break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error sending audio to Deepgram: {e}")

    async def _receive_transcripts(self) -> None:
        """Task to receive and process transcripts from Deepgram."""
        try:
            while self._is_connected and self._websocket:
                try:
                    message = await self._websocket.recv()
                    data = json.loads(message)
                    self._process_message(data)
                except ConnectionClosed:
                    logger.warning("Deepgram connection closed while receiving")
                    break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error receiving from Deepgram: {e}")

    def _process_message(self, data: dict) -> None:
        """Process a message from Deepgram."""
        msg_type = data.get("type")

        if msg_type == "Results":
            self._handle_results(data)
        elif msg_type == "Metadata":
            logger.debug(f"Deepgram metadata: {data}")
        elif msg_type == "SpeechStarted":
            logger.debug("Speech started")
        elif msg_type == "UtteranceEnd":
            logger.debug("Utterance ended")
        else:
            logger.debug(f"Unknown Deepgram message type: {msg_type}")

    def _handle_results(self, data: dict) -> None:
        """Handle transcription results."""
        channel = data.get("channel", {})
        alternatives = channel.get("alternatives", [])

        if not alternatives:
            return

        alt = alternatives[0]
        transcript = alt.get("transcript", "").strip()

        if not transcript:
            return

        # Get speaker from first word if diarization enabled
        words = alt.get("words", [])
        speaker = 0
        if words:
            speaker = words[0].get("speaker", 0)

        # Get timing info
        start_time = data.get("start", 0.0)
        duration = data.get("duration", 0.0)
        is_final = data.get("is_final", False)
        confidence = alt.get("confidence", 0.0)

        result = TranscriptResult(
            text=transcript,
            speaker=speaker,
            is_final=is_final,
            confidence=confidence,
            start_time=start_time,
            end_time=start_time + duration,
        )

        if self._transcript_callback:
            try:
                self._transcript_callback(result)
            except Exception as e:
                logger.error(f"Error in transcript callback: {e}")

    @property
    def is_connected(self) -> bool:
        """Check if connected to Deepgram."""
        return self._is_connected
