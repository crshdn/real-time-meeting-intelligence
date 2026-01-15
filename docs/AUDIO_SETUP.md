# Audio Setup Guide

This guide explains how to configure audio capture for the Real-Time Sales Assistant on different platforms.

## macOS Setup

macOS requires a virtual audio device to capture system audio (audio from other applications like Zoom, Teams, etc.).

### Prerequisites

Install **BlackHole** - a free, open-source virtual audio driver:

1. Download from: https://existential.audio/blackhole/
2. Choose **BlackHole 2ch** (2 channel version)
3. Run the installer and follow the prompts
4. Restart your Mac if prompted

### Configuration

After installing BlackHole, you need to create a **Multi-Output Device** that sends audio to both your speakers AND BlackHole.

#### Step 1: Open Audio MIDI Setup

1. Press `Cmd + Space` to open Spotlight
2. Type "Audio MIDI Setup" and press Enter
3. The Audio Devices window will open

#### Step 2: Create Multi-Output Device

1. Click the **+** button at the bottom left
2. Select **"Create Multi-Output Device"**
3. In the right panel, check the boxes for:
   - **Your speakers** (e.g., "MacBook Pro Speakers" or external speakers)
   - **BlackHole 2ch**
4. Make sure your speakers are listed FIRST (drag to reorder if needed)
5. Optionally rename it to "Sales Assistant Audio" by double-clicking the name

#### Step 3: Set System Output

1. Open **System Settings** → **Sound** → **Output**
2. Select **"Multi-Output Device"** (or your renamed device)

#### Step 4: Verify Input

1. In **System Settings** → **Sound** → **Input**
2. You can leave this as your microphone (the app captures system audio separately)

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Mac                                  │
│                                                              │
│  Zoom/Teams/Browser                                          │
│         │                                                    │
│         ▼                                                    │
│  ┌─────────────────────┐                                     │
│  │ Multi-Output Device │                                     │
│  └─────────────────────┘                                     │
│         │         │                                          │
│         ▼         ▼                                          │
│   ┌─────────┐  ┌──────────────┐                              │
│   │Speakers │  │ BlackHole 2ch│◄── Sales Assistant captures  │
│   │(you hear)│  │              │    from here                 │
│   └─────────┘  └──────────────┘                              │
└─────────────────────────────────────────────────────────────┘
```

### Troubleshooting

#### No audio being captured (all zeros)

1. **Check Multi-Output Device is selected as output**
   - System Settings → Sound → Output → Multi-Output Device

2. **Verify BlackHole is in the Multi-Output Device**
   - Open Audio MIDI Setup
   - Select your Multi-Output Device
   - Ensure BlackHole 2ch is checked

3. **Play audio to test**
   - The app only captures audio that's playing
   - Play a YouTube video or Spotify to test

4. **Run the diagnostic script**
   ```bash
   cd backend
   source .venv/bin/activate
   python debug_audio.py
   ```

#### Can't hear any audio

- Make sure your speakers are checked in the Multi-Output Device
- Make sure speakers are listed BEFORE BlackHole in the device list

#### Capturing your own microphone

BlackHole only captures system audio (other people on calls). To capture your own voice too:

1. Open Audio MIDI Setup
2. Click **+** → **"Create Aggregate Device"**
3. Check both:
   - BlackHole 2ch
   - Your microphone
4. Update the app's audio device setting to use this Aggregate Device

### Per-App Audio (Advanced)

Some apps let you choose their audio output device. You can route specific apps directly to BlackHole:

- **Zoom**: Settings → Audio → Speaker → BlackHole 2ch
- **Teams**: Settings → Devices → Speaker → BlackHole 2ch
- **Chrome**: Uses system default

---

## Windows Setup

Windows has built-in WASAPI loopback support, making setup simpler.

### Option 1: WASAPI Loopback (Recommended)

The app automatically detects WASAPI loopback devices. No additional software needed.

1. Run the app - it will auto-detect "Stereo Mix" or similar
2. If not found, enable in Sound settings:
   - Right-click speaker icon → Sounds → Recording tab
   - Right-click empty area → "Show Disabled Devices"
   - Enable "Stereo Mix" or "What U Hear"

### Option 2: Virtual Audio Cable

If WASAPI loopback isn't available:

1. Install VB-Cable: https://vb-audio.com/Cable/
2. Set VB-Cable as default playback device
3. Use "CABLE Output" as the app's input device
4. Use "VB-Cable" in your speakers setting to hear audio

---

## Linux Setup

Linux support varies by distribution.

### PulseAudio

Most Linux distros use PulseAudio which has built-in monitor devices:

1. The app will detect "Monitor of [device]" automatically
2. If not, install `pavucontrol` and enable monitoring

### PipeWire

Modern distros using PipeWire:

1. Monitor devices work similarly to PulseAudio
2. Run `pw-cli list-objects | grep -i monitor` to find devices

---

## Testing Your Setup

Run the audio test script to verify everything is working:

```bash
cd backend
source .venv/bin/activate
python test_audio_routing.py
```

This will:
1. Play a test tone through your system
2. Capture it from BlackHole/loopback
3. Report if audio is flowing correctly

If successful, you'll see: `SUCCESS: BlackHole is receiving audio!`
