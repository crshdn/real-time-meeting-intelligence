# Real-Time Sales Conversation Assistant

## Technical Specification Document

### Overview

Build a desktop application that listens to live sales calls (Zoom, Teams, or other platforms), transcribes the conversation in real-time, and provides AI-generated response suggestions, objection rebuttals, and talking points displayed on-screen for the salesperson to reference.

---

## Core Requirements

### Functional Requirements

1. **Audio Capture**: Capture system audio from video conferencing apps (Zoom, Teams, Google Meet)
2. **Real-Time Transcription**: Convert speech to text with <2 second latency
3. **Speaker Diarization**: Distinguish between the salesperson and the prospect
4. **AI Response Generation**: Analyze conversation context and generate helpful responses
5. **Low-Latency Display**: Show suggestions in an always-on-top overlay or companion window
6. **Customizable Playbook**: Allow user to input their product info, common objections, and preferred rebuttals

### Non-Functional Requirements

- Latency: End-to-end response time under 5 seconds
- Privacy: All processing should be configurable for local-only or cloud-based
- Cross-platform: Support Windows and macOS at minimum
- Unobtrusive: Overlay should not interfere with screen sharing

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User's Computer                              │
│                                                                      │
│  ┌──────────────┐    ┌──────────────────┐    ┌───────────────────┐  │
│  │   Zoom/     │    │   Audio Capture   │    │   Overlay UI      │  │
│  │   Teams     │───▶│   Module          │    │   (Always on top) │  │
│  │   Call      │    │   (System Audio)  │    │                   │  │
│  └──────────────┘    └────────┬─────────┘    └─────────▲─────────┘  │
│                               │                         │            │
│                               ▼                         │            │
│                      ┌────────────────┐                 │            │
│                      │  Audio Buffer  │                 │            │
│                      │  & Streaming   │                 │            │
│                      └────────┬───────┘                 │            │
│                               │                         │            │
└───────────────────────────────┼─────────────────────────┼────────────┘
                                │                         │
                                ▼                         │
                    ┌───────────────────────┐             │
                    │   Speech-to-Text API  │             │
                    │   (Deepgram/Assembly) │             │
                    └───────────┬───────────┘             │
                                │                         │
                                ▼                         │
                    ┌───────────────────────┐             │
                    │   Conversation Buffer │             │
                    │   + Context Manager   │             │
                    └───────────┬───────────┘             │
                                │                         │
                                ▼                         │
                    ┌───────────────────────┐             │
                    │   LLM API             │             │
                    │   (Claude/GPT-4)      │─────────────┘
                    └───────────────────────┘
```

---

## Component Specifications

### 1. Audio Capture Module

**Purpose**: Capture system audio from any application

**Technology Options**:

| Platform | Library/Tool | Notes |
|----------|--------------|-------|
| Windows | WASAPI via `sounddevice` or NAudio | Can capture system loopback audio |
| macOS | BlackHole + Core Audio | Requires virtual audio device |
| Cross-platform | `pyaudiowpatch` (Python) | Windows-focused but best option |

**Implementation Notes**:
- Capture at 16kHz sample rate (sufficient for speech, reduces bandwidth)
- Use 16-bit PCM format
- Buffer audio in 100-250ms chunks for streaming
- Handle microphone + system audio mixing for full conversation capture

**Sample Code (Python)**:
```python
import sounddevice as sd
import numpy as np
from queue import Queue

audio_queue = Queue()

def audio_callback(indata, frames, time, status):
    audio_queue.put(indata.copy())

# List available devices to find loopback
print(sd.query_devices())

# Start capture (device index varies by system)
stream = sd.InputStream(
    device=LOOPBACK_DEVICE_INDEX,
    channels=1,
    samplerate=16000,
    callback=audio_callback,
    blocksize=4000  # 250ms chunks
)
stream.start()
```

---

### 2. Speech-to-Text Service

**Recommended: Deepgram**

- Best-in-class latency (<300ms)
- Excellent accuracy for conversational speech
- Built-in speaker diarization
- Streaming WebSocket API

**Alternative: AssemblyAI**
- Slightly higher latency but excellent accuracy
- Good diarization
- Real-time streaming available

**API Integration (Deepgram)**:

```python
import asyncio
import websockets
import json

DEEPGRAM_API_KEY = "your-api-key"

async def transcribe_stream(audio_queue, transcript_callback):
    url = "wss://api.deepgram.com/v1/listen"
    params = "?encoding=linear16&sample_rate=16000&channels=1&diarize=true&punctuate=true&interim_results=true"

    async with websockets.connect(
        url + params,
        extra_headers={"Authorization": f"Token {DEEPGRAM_API_KEY}"}
    ) as ws:

        async def send_audio():
            while True:
                audio_chunk = await asyncio.get_event_loop().run_in_executor(
                    None, audio_queue.get
                )
                await ws.send(audio_chunk.tobytes())

        async def receive_transcripts():
            async for message in ws:
                data = json.loads(message)
                if data.get("is_final"):
                    transcript = data["channel"]["alternatives"][0]["transcript"]
                    speaker = data["channel"]["alternatives"][0].get("words", [{}])[0].get("speaker", 0)
                    transcript_callback(transcript, speaker)

        await asyncio.gather(send_audio(), receive_transcripts())
```

**Cost Estimate**:
- Deepgram: ~$0.0043/minute (Pay-as-you-go)
- 1-hour call = ~$0.26

---

### 3. Conversation Context Manager

**Purpose**: Maintain rolling conversation history and detect when AI assistance is needed

**Key Features**:
- Maintain last 2-3 minutes of conversation (rolling buffer)
- Detect objections, questions, and pause points
- Track speaker turns
- Identify keywords that trigger AI suggestions

**Data Structure**:
```python
from dataclasses import dataclass
from datetime import datetime
from collections import deque

@dataclass
class Utterance:
    speaker: str  # "salesperson" or "prospect"
    text: str
    timestamp: datetime

class ConversationBuffer:
    def __init__(self, max_duration_seconds=180):
        self.utterances = deque()
        self.max_duration = max_duration_seconds

    def add(self, utterance: Utterance):
        self.utterances.append(utterance)
        self._prune_old()

    def _prune_old(self):
        cutoff = datetime.now() - timedelta(seconds=self.max_duration)
        while self.utterances and self.utterances[0].timestamp < cutoff:
            self.utterances.popleft()

    def get_context_string(self) -> str:
        return "\n".join([
            f"{u.speaker}: {u.text}"
            for u in self.utterances
        ])

    def should_trigger_ai(self) -> bool:
        """Detect if we should generate a suggestion"""
        if not self.utterances:
            return False

        last = self.utterances[-1]

        # Trigger on prospect speech ending (potential objection/question)
        if last.speaker == "prospect":
            return True

        # Trigger on certain keywords
        trigger_phrases = [
            "too expensive", "not sure", "competitor",
            "think about it", "not the right time", "budget"
        ]
        recent_text = " ".join([u.text.lower() for u in list(self.utterances)[-3:]])
        return any(phrase in recent_text for phrase in trigger_phrases)
```

---

### 4. LLM Response Generator

**Purpose**: Generate contextual response suggestions

**Recommended: Claude API (Anthropic)**
- Excellent at nuanced conversation understanding
- Good at role-playing sales scenarios
- Fast response times with streaming

**Alternative: GPT-4 Turbo**
- Also excellent, slightly different style
- Good streaming support

**System Prompt Template**:

```markdown
You are a real-time sales assistant helping a salesperson during a live call.

## Your Role
- Provide 2-3 concise response suggestions when the prospect raises objections or asks questions
- Keep suggestions brief (1-2 sentences each) so they can be quickly read
- Focus on overcoming objections and moving the conversation forward
- Match the tone to the conversation (professional but natural)

## Product/Service Context
{product_description}

## Common Objections & Recommended Responses
{objection_playbook}

## Key Value Propositions
{value_props}

## Current Conversation
{conversation_transcript}

## Instructions
The prospect just said: "{last_prospect_statement}"

Provide 2-3 response options the salesperson could use. Format as:
1. [Response option 1]
2. [Response option 2]
3. [Response option 3 - optional]

Keep each under 30 words. Focus on the most effective response first.
```

**API Integration**:

```python
import anthropic

client = anthropic.Anthropic(api_key="your-api-key")

async def generate_suggestions(
    conversation_context: str,
    last_statement: str,
    playbook: dict
) -> str:

    system_prompt = SYSTEM_TEMPLATE.format(
        product_description=playbook["product"],
        objection_playbook=playbook["objections"],
        value_props=playbook["value_props"],
        conversation_transcript=conversation_context,
        last_prospect_statement=last_statement
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        system=system_prompt,
        messages=[
            {"role": "user", "content": "Generate response suggestions now."}
        ]
    )

    return response.content[0].text
```

**Cost Estimate**:
- Claude Sonnet: ~$3/million input tokens, $15/million output tokens
- Typical call with 50 suggestions: ~$0.10-0.20

---

### 5. Overlay UI

**Purpose**: Display suggestions unobtrusively during calls

**Technology Options**:

| Approach | Pros | Cons |
|----------|------|------|
| Electron + React | Cross-platform, rich UI | Heavier resource usage |
| Tauri + Svelte | Lightweight, native feel | Smaller ecosystem |
| Python + PyQt/Tkinter | Simple, single language | Less polished UI |
| Web app + OBS overlay | No install needed | More complex setup |

**Recommended: Electron + React**

**UI Requirements**:
- Always-on-top window (configurable)
- Transparent/semi-transparent background
- Resizable and draggable
- Can be positioned on secondary monitor
- Shows: current transcript line, 2-3 AI suggestions
- Click-to-copy for suggestions
- Minimize to system tray

**Wireframe**:
```
┌─────────────────────────────────────────────┐
│  🎯 Sales Assistant                    ─ □ x │
├─────────────────────────────────────────────┤
│                                             │
│  PROSPECT: "That's more than we budgeted   │
│  for this quarter..."                       │
│                                             │
├─────────────────────────────────────────────┤
│  💡 SUGGESTED RESPONSES:                    │
│                                             │
│  1. "I understand budget timing. Many       │
│     clients split this across Q1 and Q2 -  │
│     would that work for you?"              │
│                                        [📋] │
│                                             │
│  2. "What if we started with the core      │
│     package now and added features later?" │
│                                        [📋] │
│                                             │
│  3. "Can you share what budget range       │
│     would work? I may have options."       │
│                                        [📋] │
│                                             │
└─────────────────────────────────────────────┘
```

**Sample React Component**:

```jsx
import React, { useState, useEffect } from 'react';

function SuggestionOverlay() {
  const [transcript, setTranscript] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [isListening, setIsListening] = useState(false);

  useEffect(() => {
    // Connect to backend WebSocket
    const ws = new WebSocket('ws://localhost:8765');

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'transcript') {
        setTranscript(data.text);
      } else if (data.type === 'suggestions') {
        setSuggestions(data.items);
      }
    };

    return () => ws.close();
  }, []);

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  return (
    
      
        PROSPECT:
        {transcript}
      

      
        💡 Suggested Responses:
        {suggestions.map((suggestion, index) => (
          
            {index + 1}. {suggestion}
            <button onClick={() => copyToClipboard(suggestion)}>
              📋
            
          
        ))}
      
    
  );
}
```

---

## Configuration & Playbook

**User Configuration File (JSON)**:

```json
{
  "user_settings": {
    "my_speaker_label": "You",
    "overlay_position": "bottom-right",
    "overlay_opacity": 0.95,
    "always_on_top": true,
    "hotkey_toggle": "Ctrl+Shift+S"
  },

  "product_context": {
    "product_name": "Acme CRM Pro",
    "description": "Enterprise CRM solution with AI-powered lead scoring, automated follow-ups, and deep analytics integration.",
    "target_audience": "Mid-market B2B companies with 50-500 employees",
    "pricing_tiers": [
      {"name": "Starter", "price": "$50/user/month"},
      {"name": "Professional", "price": "$100/user/month"},
      {"name": "Enterprise", "price": "Custom"}
    ]
  },

  "value_propositions": [
    "Reduces manual data entry by 80%",
    "Increases sales team productivity by 35%",
    "Integrates with 200+ tools out of the box",
    "Implementation in under 2 weeks"
  ],

  "objection_playbook": {
    "too_expensive": {
      "triggers": ["too expensive", "over budget", "can't afford", "too much"],
      "responses": [
        "Reframe as ROI: Ask about cost of current manual processes",
        "Offer phased implementation to spread costs",
        "Highlight hidden costs of not switching"
      ]
    },
    "need_to_think": {
      "triggers": ["think about it", "get back to you", "discuss internally"],
      "responses": [
        "Ask what specific concerns need discussion",
        "Offer to join internal meeting to answer questions",
        "Set specific follow-up time before ending call"
      ]
    },
    "using_competitor": {
      "triggers": ["already using", "have a solution", "competitor name"],
      "responses": [
        "Ask what they wish was better about current solution",
        "Offer comparison or migration support",
        "Share relevant case study of similar switch"
      ]
    },
    "bad_timing": {
      "triggers": ["not the right time", "too busy", "next quarter"],
      "responses": [
        "Ask what would need to change for timing to be right",
        "Offer lighter-touch pilot program",
        "Discuss cost of waiting (competitor advantage, etc.)"
      ]
    }
  }
}
```

---

## Development Phases

### Phase 1: MVP (2-3 weeks)
- [ ] Basic audio capture (system audio on Windows or Mac)
- [ ] Deepgram integration for real-time transcription
- [ ] Simple Claude API integration with basic prompt
- [ ] Minimal Electron overlay showing suggestions
- [ ] Hardcoded product context

### Phase 2: Core Features (2-3 weeks)
- [ ] Speaker diarization (distinguish salesperson from prospect)
- [ ] Configurable playbook via JSON/UI
- [ ] Improved objection detection
- [ ] Copy-to-clipboard for suggestions
- [ ] System tray with start/stop controls

### Phase 3: Polish (2-3 weeks)
- [ ] Cross-platform support (Windows + Mac)
- [ ] UI settings panel
- [ ] Conversation history/logging
- [ ] Analytics dashboard (objections encountered, suggestions used)
- [ ] Hotkey controls

### Phase 4: Advanced (Optional)
- [ ] Local LLM option (Ollama) for privacy
- [ ] Local Whisper for offline transcription
- [ ] CRM integration (auto-log calls)
- [ ] Team features (shared playbooks)
- [ ] Sentiment analysis

---

## Tech Stack Summary

| Component | Recommended | Alternative |
|-----------|-------------|-------------|
| Language | Python (backend) + TypeScript (UI) | All TypeScript |
| Audio Capture | `sounddevice` / WASAPI | PortAudio |
| Speech-to-Text | Deepgram (streaming) | AssemblyAI, Whisper API |
| LLM | Claude API | GPT-4 Turbo |
| Desktop UI | Electron + React | Tauri + Svelte |
| IPC | WebSocket (localhost) | Electron IPC |

---

## API Keys Required

1. **Deepgram** - https://console.deepgram.com/ (free tier available)
2. **Anthropic (Claude)** - https://console.anthropic.com/ (requires payment method)

---

## Security & Privacy Considerations

1. **Audio Data**: Never store raw audio unless explicitly enabled
2. **Transcripts**: Offer local-only mode where transcripts don't leave device
3. **API Keys**: Store encrypted, not in plaintext config
4. **Screen Sharing**: Warn user if overlay is visible during screen share
5. **Compliance**: Add disclaimer about call recording consent laws

---

## Estimated Costs (Per Month)

| Usage Level | Deepgram | Claude API | Total |
|-------------|----------|------------|-------|
| Light (10 hrs/month) | ~$2.50 | ~$2 | ~$5 |
| Medium (40 hrs/month) | ~$10 | ~$8 | ~$18 |
| Heavy (100 hrs/month) | ~$25 | ~$20 | ~$45 |

---

## Getting Started

```bash
# Clone repo
git clone https://github.com/your-org/sales-assistant.git
cd sales-assistant

# Install Python dependencies
pip install anthropic deepgram-sdk sounddevice websockets

# Install Node dependencies for UI
cd ui
npm install

# Set up environment variables
export DEEPGRAM_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"

# Run backend
python main.py

# Run UI (separate terminal)
cd ui
npm start
```

---

## Questions for Product Owner

Before development begins, clarify:

1. **Platform priority**: Windows first, Mac first, or both simultaneously?
2. **Privacy requirements**: Cloud-only OK, or need local/offline option?
3. **Customization depth**: Simple playbook editing, or full prompt customization?
4. **Team features**: Single user only, or multi-user with shared playbooks?
5. **Integration needs**: Any CRM integration required for MVP?

---
