# Start Development Environment

Start both backend and frontend development servers.

## Steps

1. Check that environment variables are set
2. Start the Python backend WebSocket server
3. Start the Electron/React development server
4. Verify connections are working

## Commands

```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
python main.py

# Terminal 2 - Frontend
cd ui
npm run dev
```

## Verification

- Backend: WebSocket server listening on ws://localhost:8765
- Frontend: Electron window opens with overlay UI
- Connection: Frontend shows "Connected" status
