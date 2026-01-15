# Test Audio Capture

Test that system audio capture is working correctly.

## Steps

1. List available audio devices
2. Identify the loopback/system audio device
3. Test capturing audio from the device
4. Verify audio data is being received

## Commands

```bash
cd backend
python -c "import sounddevice as sd; print(sd.query_devices())"
```

## Expected Output

Look for devices with "loopback", "stereo mix", or "what u hear" in the name.

On macOS with BlackHole:
- "BlackHole 2ch" or "BlackHole 16ch"

On Windows:
- "Stereo Mix" or system loopback device

## Troubleshooting

### macOS
- Install BlackHole: `brew install blackhole-2ch`
- Set up Multi-Output Device in Audio MIDI Setup
- Route system audio through BlackHole

### Windows
- Enable Stereo Mix in Sound settings
- Or use WASAPI loopback mode (automatic)
