import { useState, useCallback } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import { StatusBar } from './components/StatusBar';
import { TranscriptPanel } from './components/TranscriptPanel';
import { SuggestionList } from './components/SuggestionList';
import type { ServerMessage } from './types';

const WEBSOCKET_URL = 'ws://localhost:8765';

function App() {
  const [isListening, setIsListening] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [currentTranscript, setCurrentTranscript] = useState('');
  const [currentSpeaker, setCurrentSpeaker] = useState<string>('');
  const [suggestions, setSuggestions] = useState<string[]>([]);

  const handleMessage = useCallback((message: ServerMessage) => {
    switch (message.type) {
      case 'transcript':
        setCurrentTranscript(message.text);
        setCurrentSpeaker(message.speaker);
        break;

      case 'suggestions':
        setSuggestions(message.items);
        break;

      case 'status':
        setIsListening(message.listening);
        setIsTranscribing(message.transcribing);
        break;

      case 'ack':
        console.log('Command acknowledged:', message.success);
        break;

      case 'error':
        console.error('Server error:', message.message);
        break;
    }
  }, []);

  const handleConnect = useCallback(() => {
    console.log('Connected to backend');
  }, []);

  const handleDisconnect = useCallback(() => {
    console.log('Disconnected from backend');
    setIsListening(false);
    setIsTranscribing(false);
  }, []);

  const { isConnected, send } = useWebSocket({
    url: WEBSOCKET_URL,
    onMessage: handleMessage,
    onConnect: handleConnect,
    onDisconnect: handleDisconnect,
  });

  const handleToggleListening = useCallback(() => {
    if (isListening) {
      send({ type: 'stop_listening' });
    } else {
      send({ type: 'start_listening' });
    }
  }, [isListening, send]);

  const handleCopySuggestion = useCallback(async (text: string) => {
    try {
      // Try Electron API first (if available)
      if (window.electronAPI?.copyToClipboard) {
        await window.electronAPI.copyToClipboard(text);
      } else {
        // Fallback to browser clipboard API
        await navigator.clipboard.writeText(text);
      }
      return true;
    } catch (e) {
      console.error('Failed to copy:', e);
      return false;
    }
  }, []);

  return (
    <div className="h-full flex flex-col bg-overlay-bg rounded-xl border border-overlay-border overflow-hidden shadow-2xl">
      {/* Title bar / Status bar */}
      <StatusBar
        isConnected={isConnected}
        isListening={isListening}
        isTranscribing={isTranscribing}
        onToggleListening={handleToggleListening}
      />

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden p-4 pt-2 gap-4">
        {/* Transcript panel */}
        <TranscriptPanel
          transcript={currentTranscript}
          speaker={currentSpeaker}
          isListening={isListening}
        />

        {/* Suggestions */}
        <SuggestionList
          suggestions={suggestions}
          onCopy={handleCopySuggestion}
        />
      </div>
    </div>
  );
}

export default App;
