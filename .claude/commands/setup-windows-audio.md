# Setup Windows Audio Capture

Configure Windows for system audio capture using WASAPI loopback.

## Option 1: Stereo Mix (Simple)

1. Right-click speaker icon in taskbar → **Sounds**
2. Go to **Recording** tab
3. Right-click empty space → **Show Disabled Devices**
4. Find **Stereo Mix** → Right-click → **Enable**
5. Set as default device (optional)

## Option 2: WASAPI Loopback (Recommended)

No setup needed - `sounddevice` with `pyaudiowpatch` can capture directly.

```bash
pip install pyaudiowpatch
```

The library automatically finds the loopback device.

## Find Device Index

```bash
python -c "import sounddevice as sd; print(sd.query_devices())"
```

Look for devices with:
- "Stereo Mix"
- "WASAPI" and "loopback" in name
- Your speaker device (for loopback capture)

## Set in Environment

```
AUDIO_DEVICE_INDEX=<number>
```

Or leave as `auto` to auto-detect.

## Verify Setup

```bash
cd backend
python .claude/snippets/audio-capture.py
```

Play audio from any application - you should see sample counts.

## Capturing Both System + Microphone

To capture both sides of the conversation:

1. Use two input streams:
   - One for system audio (loopback)
   - One for microphone

2. Mix them in software before sending to Deepgram

Or use a virtual audio mixer like VoiceMeeter.

## Troubleshooting

### Stereo Mix not visible
- Update audio drivers
- Some audio chips don't support it
- Use WASAPI loopback instead

### No audio captured
- Check correct device index
- Verify audio is playing
- Try different sample rates (44100, 48000)

### Permission denied
- Run as Administrator
- Check Windows privacy settings for microphone
