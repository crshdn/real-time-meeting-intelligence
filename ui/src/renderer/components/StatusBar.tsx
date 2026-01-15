import { useCallback } from 'react';

interface StatusBarProps {
  isConnected: boolean;
  isListening: boolean;
  isTranscribing: boolean;
  onToggleListening: () => void;
}

export function StatusBar({
  isConnected,
  isListening,
  isTranscribing,
  onToggleListening,
}: StatusBarProps) {
  const handleMinimize = useCallback(() => {
    window.electronAPI?.minimize();
  }, []);

  const handleClose = useCallback(() => {
    window.electronAPI?.close();
  }, []);

  return (
    <div className="titlebar-drag flex items-center justify-between px-4 py-2 bg-zinc-900/50 border-b border-white/5">
      {/* Left: Title and status */}
      <div className="flex items-center gap-3">
        <h1 className="text-sm font-semibold text-white/90">Sales Assistant</h1>

        {/* Connection status dot */}
        <div className="flex items-center gap-1.5">
          <div
            className={`w-2 h-2 rounded-full ${
              isConnected
                ? isTranscribing
                  ? 'bg-green-400 status-dot-pulse'
                  : 'bg-green-400'
                : 'bg-red-400'
            }`}
          />
          <span className="text-xs text-white/50">
            {!isConnected
              ? 'Disconnected'
              : isTranscribing
              ? 'Transcribing'
              : isListening
              ? 'Listening'
              : 'Ready'}
          </span>
        </div>
      </div>

      {/* Right: Controls */}
      <div className="titlebar-no-drag flex items-center gap-2">
        {/* Listen toggle button */}
        <button
          onClick={onToggleListening}
          disabled={!isConnected}
          className={`px-3 py-1 text-xs font-medium rounded transition-colors ${
            isListening
              ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
              : 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {isListening ? 'Stop' : 'Start'}
        </button>

        {/* Window controls */}
        <div className="flex items-center gap-1 ml-2">
          <button
            onClick={handleMinimize}
            className="w-6 h-6 flex items-center justify-center rounded hover:bg-white/10 transition-colors"
            title="Minimize"
          >
            <svg className="w-3 h-3 text-white/60" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
            </svg>
          </button>
          <button
            onClick={handleClose}
            className="w-6 h-6 flex items-center justify-center rounded hover:bg-red-500/20 transition-colors"
            title="Close"
          >
            <svg className="w-3 h-3 text-white/60" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
