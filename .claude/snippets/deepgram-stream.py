# Deepgram Streaming Transcription Snippet
# Real-time speech-to-text with WebSocket

import asyncio
import websockets
import json
import os
from queue import Queue

DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY")

async def transcribe_stream(audio_queue: Queue, transcript_callback):
    """
    Stream audio to Deepgram and receive real-time transcriptions.

    Args:
        audio_queue: Queue containing audio chunks (numpy arrays)
        transcript_callback: Function called with (transcript, speaker, is_final)
    """
    url = "wss://api.deepgram.com/v1/listen"
    params = "?".join([
        "",
        "encoding=linear16",
        "sample_rate=16000",
        "channels=1",
        "diarize=true",
        "punctuate=true",
        "interim_results=true",
        "endpointing=300",
        "vad_events=true"
    ]).replace("?", "&")[1:]

    headers = {"Authorization": f"Token {DEEPGRAM_API_KEY}"}

    async with websockets.connect(url + "?" + params, extra_headers=headers) as ws:

        async def send_audio():
            """Send audio chunks to Deepgram."""
            while True:
                # Get audio from queue (blocking)
                audio_chunk = await asyncio.get_event_loop().run_in_executor(
                    None, audio_queue.get
                )
                if audio_chunk is None:  # Sentinel to stop
                    await ws.send(json.dumps({"type": "CloseStream"}))
                    break
                await ws.send(audio_chunk.tobytes())

        async def receive_transcripts():
            """Receive and process transcription results."""
            async for message in ws:
                data = json.loads(message)

                # Handle transcription results
                if data.get("type") == "Results":
                    channel = data.get("channel", {})
                    alternatives = channel.get("alternatives", [{}])

                    if alternatives:
                        transcript = alternatives[0].get("transcript", "")
                        words = alternatives[0].get("words", [])
                        is_final = data.get("is_final", False)

                        # Get speaker from first word if diarization enabled
                        speaker = words[0].get("speaker", 0) if words else 0

                        if transcript.strip():
                            transcript_callback(transcript, speaker, is_final)

        # Run send and receive concurrently
        await asyncio.gather(send_audio(), receive_transcripts())


def on_transcript(transcript: str, speaker: int, is_final: bool):
    """Example callback for transcripts."""
    speaker_label = "Speaker " + str(speaker)
    status = "FINAL" if is_final else "interim"
    print(f"[{status}] {speaker_label}: {transcript}")


# Usage example:
if __name__ == "__main__":
    from queue import Queue

    audio_queue = Queue()

    # In real usage, populate audio_queue from audio capture
    # audio_queue.put(audio_chunk)

    asyncio.run(transcribe_stream(audio_queue, on_transcript))
