"""
Audio Capture Module for Real-Time Sales Assistant.
Captures system audio using sounddevice with loopback support.
"""

import asyncio
import logging
import platform
from typing import Optional, Callable, Any
from queue import Queue, Empty
import threading

import numpy as np
import sounddevice as sd

logger = logging.getLogger(__name__)


class AudioCapture:
    """
    System audio capture using sounddevice.
    Supports macOS (via BlackHole) and Windows (via WASAPI loopback).
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        blocksize: int = 4000,  # 250ms at 16kHz
        device_index: Optional[int] = None,
    ):
        """
        Initialize audio capture.

        Args:
            sample_rate: Sample rate in Hz (16000 recommended for speech)
            channels: Number of channels (1 for mono)
            blocksize: Samples per block (4000 = 250ms at 16kHz)
            device_index: Specific device index, or None for auto-detect
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.blocksize = blocksize
        self.device_index = device_index

        self._stream: Optional[sd.InputStream] = None
        self._audio_queue: Queue = Queue()
        self._is_running = False
        self._error_callback: Optional[Callable] = None

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: Any,
        status: sd.CallbackFlags,
    ) -> None:
        """Callback for audio stream - adds chunks to queue."""
        if status:
            logger.warning(f"Audio callback status: {status}")
            if self._error_callback:
                self._error_callback(str(status))

        # Convert to int16 if needed and add to queue
        if indata.dtype != np.int16:
            audio_data = (indata * 32767).astype(np.int16)
        else:
            audio_data = indata.copy()

        self._audio_queue.put(audio_data)

    @staticmethod
    def list_devices() -> list[dict]:
        """List all available audio devices."""
        devices = sd.query_devices()
        return [
            {
                "index": i,
                "name": d["name"],
                "channels": d["max_input_channels"],
                "sample_rate": d["default_samplerate"],
            }
            for i, d in enumerate(devices)
            if d["max_input_channels"] > 0
        ]

    @staticmethod
    def find_loopback_device() -> Optional[int]:
        """
        Auto-detect system loopback device.

        Returns:
            Device index or None if not found
        """
        devices = sd.query_devices()
        system = platform.system()

        # Keywords to search for
        if system == "Darwin":  # macOS
            keywords = ["blackhole", "soundflower", "loopback"]
        elif system == "Windows":
            keywords = ["loopback", "stereo mix", "what u hear", "wave out"]
        else:
            keywords = ["loopback", "monitor"]

        for i, device in enumerate(devices):
            name = device["name"].lower()
            if device["max_input_channels"] > 0:
                for keyword in keywords:
                    if keyword in name:
                        logger.info(f"Found loopback device: {device['name']} (index {i})")
                        return i

        logger.warning("No loopback device found automatically")
        return None

    def start(self, error_callback: Optional[Callable] = None) -> None:
        """
        Start audio capture.

        Args:
            error_callback: Optional callback for audio errors
        """
        if self._is_running:
            logger.warning("Audio capture already running")
            return

        self._error_callback = error_callback

        # Auto-detect device if not specified
        device = self.device_index
        if device is None:
            device = self.find_loopback_device()
            if device is None:
                # Fall back to default input device
                device = sd.default.device[0]
                logger.warning(f"Using default input device: {device}")

        try:
            self._stream = sd.InputStream(
                device=device,
                channels=self.channels,
                samplerate=self.sample_rate,
                callback=self._audio_callback,
                blocksize=self.blocksize,
                dtype=np.int16,
            )
            self._stream.start()
            self._is_running = True
            logger.info(
                f"Audio capture started (device={device}, "
                f"rate={self.sample_rate}, blocksize={self.blocksize})"
            )
        except Exception as e:
            logger.error(f"Failed to start audio capture: {e}")
            raise

    def stop(self) -> None:
        """Stop audio capture."""
        if not self._is_running:
            return

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        self._is_running = False
        # Clear queue
        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
            except Empty:
                break

        logger.info("Audio capture stopped")

    def get_chunk(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """
        Get next audio chunk from queue (blocking).

        Args:
            timeout: Maximum seconds to wait

        Returns:
            Audio data as numpy array, or None if timeout
        """
        try:
            return self._audio_queue.get(timeout=timeout)
        except Empty:
            return None

    async def get_chunk_async(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """
        Get next audio chunk asynchronously.

        Args:
            timeout: Maximum seconds to wait

        Returns:
            Audio data as numpy array, or None if timeout
        """
        loop = asyncio.get_event_loop()
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(None, self._audio_queue.get),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            return None

    @property
    def is_running(self) -> bool:
        """Check if capture is currently running."""
        return self._is_running

    @property
    def queue_size(self) -> int:
        """Get current queue size."""
        return self._audio_queue.qsize()

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False
