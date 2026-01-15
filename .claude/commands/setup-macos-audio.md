# Setup macOS Audio Capture

Configure macOS for system audio capture using BlackHole.

## Install BlackHole

```bash
brew install blackhole-2ch
```

Or download from: https://existential.audio/blackhole/

## Configure Multi-Output Device

1. Open **Audio MIDI Setup** (Applications > Utilities)
2. Click **+** button at bottom left
3. Select **Create Multi-Output Device**
4. Check both:
   - Your speakers/headphones
   - BlackHole 2ch
5. Right-click the Multi-Output Device → **Use This Device For Sound Output**

## Configure Aggregate Device (for mic + system)

1. In Audio MIDI Setup, click **+**
2. Select **Create Aggregate Device**
3. Check:
   - BlackHole 2ch (for system audio)
   - Your microphone (for your voice)
4. Name it "Sales Assistant Input"

## Set Input Device in App

In `.env`:
```
AUDIO_DEVICE_INDEX=auto
```

Or find the device index:
```bash
python -c "import sounddevice as sd; print(sd.query_devices())"
```

Look for "BlackHole" or your aggregate device name.

## Verify Setup

```bash
# Test audio capture
cd backend
python .claude/snippets/audio-capture.py
```

Play some audio - you should see "Got X samples" messages.

## Troubleshooting

### No audio captured
- Ensure Multi-Output Device is set as system output
- Check BlackHole is included in the device

### Can't hear audio
- Ensure speakers are included in Multi-Output Device
- Check master volume isn't muted

### Echo in recordings
- Don't include speakers in Aggregate Input Device
- Only use BlackHole for system audio capture
