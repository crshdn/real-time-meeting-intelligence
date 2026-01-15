interface TranscriptPanelProps {
  transcript: string;
  speaker: string;
  isListening: boolean;
}

export function TranscriptPanel({
  transcript,
  speaker,
  isListening,
}: TranscriptPanelProps) {
  const speakerLabel = speaker === 'prospect' ? 'PROSPECT' : speaker === 'salesperson' ? 'YOU' : '';

  return (
    <div className="flex-shrink-0 bg-zinc-800/50 rounded-lg p-3 border border-white/5">
      {transcript ? (
        <>
          {/* Speaker label */}
          {speakerLabel && (
            <div className={`text-xs font-semibold mb-1.5 ${
              speaker === 'prospect' ? 'text-blue-400' : 'text-emerald-400'
            }`}>
              {speakerLabel}
            </div>
          )}

          {/* Transcript text */}
          <p className="text-sm text-white/90 leading-relaxed">
            "{transcript}"
          </p>
        </>
      ) : (
        <div className="text-sm text-white/40 italic text-center py-2">
          {isListening
            ? 'Listening for speech...'
            : 'Click "Start" to begin listening'}
        </div>
      )}
    </div>
  );
}
