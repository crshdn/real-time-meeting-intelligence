# Real-Time Sales Conversation Assistant

A desktop application that listens to live sales calls (Zoom, Teams, Google Meet), transcribes in real-time, and provides AI-generated response suggestions displayed in an overlay.

## Features

- **Real-time transcription** - Powered by Deepgram's Nova-2 model
- **Speaker diarization** - Distinguishes between you and the prospect
- **AI suggestions** - Claude generates contextual response suggestions
- **Overlay UI** - Always-on-top, draggable overlay that doesn't interfere with screen sharing
- **Cross-platform** - Works on macOS and Windows

## Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **macOS**: BlackHole virtual audio driver ([download](https://existential.audio/blackhole/))
- **API Keys**:
  - [Deepgram](https://console.deepgram.com/) - for transcription
  - [Anthropic](https://console.anthropic.com/) - for AI suggestions

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/real-time-meeting-intelligence.git
   cd real-time-meeting-intelligence
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

3. **Install backend dependencies**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Install frontend dependencies**
   ```bash
   cd ../ui
   npm install
   ```

5. **Configure audio** (macOS only)

   See [Audio Setup Guide](docs/AUDIO_SETUP.md) for detailed instructions.

   Quick version:
   - Install BlackHole 2ch
   - Create a Multi-Output Device in Audio MIDI Setup
   - Set Multi-Output Device as system output

### Running the App

1. **Start the backend** (in one terminal)
   ```bash
   cd backend
   source .venv/bin/activate
   python main.py
   ```

2. **Start the frontend** (in another terminal)
   ```bash
   cd ui
   npm run dev
   ```

3. **Click "Start Listening"** in the overlay UI

4. **Join a call** and start your conversation!

## How It Works

```
┌──────────────────────────────────────────────────────────────────┐
│                         Your Computer                             │
│                                                                   │
│  ┌─────────────┐    ┌─────────────────┐    ┌──────────────────┐  │
│  │ Zoom/Teams  │───►│  Audio Capture  │───►│    Deepgram      │  │
│  │  (call)     │    │  (BlackHole)    │    │  (transcription) │  │
│  └─────────────┘    └─────────────────┘    └────────┬─────────┘  │
│                                                      │            │
│                                                      ▼            │
│  ┌─────────────┐    ┌─────────────────┐    ┌──────────────────┐  │
│  │  Overlay UI │◄───│ WebSocket Server│◄───│     Claude       │  │
│  │ (suggestions)│   │  (localhost)    │    │  (AI suggestions)│  │
│  └─────────────┘    └─────────────────┘    └──────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

1. **Audio Capture**: System audio is captured via BlackHole (macOS) or WASAPI (Windows)
2. **Transcription**: Audio streams to Deepgram for real-time speech-to-text
3. **Context Management**: Transcripts are buffered and analyzed for trigger phrases
4. **AI Suggestions**: When objections are detected, Claude generates response suggestions
5. **Overlay Display**: Suggestions appear in a non-intrusive overlay

## Project Structure

```
real-time-meeting-intelligence/
├── backend/
│   ├── main.py              # Application entry point
│   ├── audio_capture.py     # System audio capture
│   ├── transcription.py     # Deepgram integration
│   ├── context_manager.py   # Conversation buffer & triggers
│   ├── llm_generator.py     # Claude API integration
│   ├── websocket_server.py  # Frontend communication
│   └── requirements.txt
├── ui/
│   ├── src/
│   │   ├── main/            # Electron main process
│   │   ├── renderer/        # React components
│   │   └── shared/          # Shared TypeScript types
│   └── package.json
├── config/
│   └── playbook.example.json  # Sales playbook template
├── docs/
│   └── AUDIO_SETUP.md       # Audio configuration guide
├── .env.example             # Environment variables template
└── README.md
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DEEPGRAM_API_KEY` | Yes | Your Deepgram API key |
| `ANTHROPIC_API_KEY` | Yes | Your Anthropic API key |
| `WEBSOCKET_PORT` | No | WebSocket port (default: 8765) |
| `DEBUG` | No | Enable debug logging (0 or 1) |

### Sales Playbook

Customize AI suggestions by editing `config/playbook.json`:

```json
{
  "company": "Your Company",
  "product": "Your Product",
  "objection_handlers": {
    "price": "Focus on ROI and value...",
    "competitor": "Highlight unique differentiators..."
  }
}
```

## Development

### Backend Commands

```bash
cd backend
source .venv/bin/activate

# Run with debug logging
DEBUG=1 python main.py

# Run tests
pytest tests/

# Audio diagnostics
python debug_audio.py
python test_audio_routing.py
```

### Frontend Commands

```bash
cd ui

# Development mode (hot reload)
npm run dev

# Type checking
npm run typecheck

# Build for production
npm run build

# Package as desktop app
npm run package
```

## Troubleshooting

### No audio being captured

1. Verify BlackHole is installed: `ls /Library/Audio/Plug-Ins/HAL/`
2. Check Multi-Output Device is set as system output
3. Run `python debug_audio.py` to diagnose

### Transcription not working

1. Check Deepgram API key is valid
2. Verify network connection to api.deepgram.com
3. Check backend logs for errors

### UI not connecting

1. Ensure backend is running on port 8765
2. Check for port conflicts: `lsof -i :8765`
3. Verify WebSocket connection in browser dev tools

### High latency

- Use wired internet connection
- Close unnecessary browser tabs
- Check Deepgram dashboard for API latency

## Privacy & Security

- **No audio storage**: Raw audio is never saved to disk
- **Local processing**: All communication happens over localhost
- **API keys**: Stored in `.env` (gitignored)
- **Transcripts**: Optionally saved, can be disabled

**Important**: Always inform call participants about recording/transcription according to local laws.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [Deepgram](https://deepgram.com/) - Real-time speech recognition
- [Anthropic](https://anthropic.com/) - Claude AI
- [BlackHole](https://existential.audio/blackhole/) - Virtual audio driver
- [Electron](https://electronjs.org/) - Desktop framework
