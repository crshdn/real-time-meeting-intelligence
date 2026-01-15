# Debug Transcription

Test Deepgram transcription without the full application.

## Quick Test

```bash
cd backend
python -c "
import os
from deepgram import Deepgram

dg = Deepgram(os.environ.get('DEEPGRAM_API_KEY'))

# Test with a sample audio URL
source = {'url': 'https://static.deepgram.com/examples/Bueller-Life-moves-702.wav'}
response = dg.transcription.sync_prerecorded(source, {'punctuate': True})
print(response['results']['channels'][0]['alternatives'][0]['transcript'])
"
```

## Stream Test

```bash
cd backend
python snippets/deepgram-stream.py
```

## Troubleshooting

### "401 Unauthorized"
- Check DEEPGRAM_API_KEY is set and valid
- Verify key hasn't expired

### "Connection refused"
- Check internet connection
- Verify WebSocket port isn't blocked

### No transcript output
- Verify audio is 16kHz, 16-bit PCM
- Check audio isn't silent or too quiet
- Try increasing audio gain
