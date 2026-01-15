# Audio Capture Snippet
# System audio capture using sounddevice

import sounddevice as sd
import numpy as np
from queue import Queue
import threading

audio_queue = Queue()

def audio_callback(indata, frames, time, status):
    """Callback for audio stream - adds chunks to queue."""
    if status:
        print(f"Audio status: {status}")
    audio_queue.put(indata.copy())

def list_audio_devices():
    """List all available audio devices."""
    print(sd.query_devices())

def find_loopback_device():
    """Find system loopback device index."""
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        name = device['name'].lower()
        if any(term in name for term in ['loopback', 'stereo mix', 'blackhole', 'what u hear']):
            return i
    return None

def start_capture(device_index=None, sample_rate=16000, channels=1, blocksize=4000):
    """
    Start capturing audio.

    Args:
        device_index: Audio device index (None for default)
        sample_rate: Sample rate in Hz (16000 recommended for speech)
        channels: Number of channels (1 for mono)
        blocksize: Samples per block (4000 = 250ms at 16kHz)

    Returns:
        InputStream object
    """
    stream = sd.InputStream(
        device=device_index,
        channels=channels,
        samplerate=sample_rate,
        callback=audio_callback,
        blocksize=blocksize,
        dtype=np.int16
    )
    stream.start()
    return stream

def get_audio_chunk(timeout=1.0):
    """Get next audio chunk from queue."""
    try:
        return audio_queue.get(timeout=timeout)
    except:
        return None

# Usage example:
if __name__ == "__main__":
    list_audio_devices()
    device = find_loopback_device()
    print(f"Using device: {device}")

    stream = start_capture(device)
    try:
        while True:
            chunk = get_audio_chunk()
            if chunk is not None:
                print(f"Got {len(chunk)} samples")
    except KeyboardInterrupt:
        stream.stop()
        stream.close()
