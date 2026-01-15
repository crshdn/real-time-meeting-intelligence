import { useState, useCallback } from 'react';

interface SuggestionListProps {
  suggestions: string[];
  onCopy: (text: string) => Promise<boolean>;
}

export function SuggestionList({ suggestions, onCopy }: SuggestionListProps) {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const handleCopy = useCallback(async (text: string, index: number) => {
    const success = await onCopy(text);
    if (success) {
      setCopiedIndex(index);
      setTimeout(() => setCopiedIndex(null), 1500);
    }
  }, [onCopy]);

  if (suggestions.length === 0) {
    return (
      <div className="flex-1 flex flex-col">
        <h2 className="text-xs font-semibold text-white/50 uppercase tracking-wider mb-2">
          Suggested Responses
        </h2>
        <div className="flex-1 flex items-center justify-center">
          <p className="text-sm text-white/30 italic">
            Suggestions will appear here
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col min-h-0">
      <h2 className="text-xs font-semibold text-white/50 uppercase tracking-wider mb-2 flex items-center gap-2">
        <span className="text-yellow-400/80">💡</span>
        Suggested Responses
      </h2>

      <div className="flex-1 overflow-y-auto space-y-2">
        {suggestions.map((suggestion, index) => (
          <div
            key={index}
            className="suggestion-item group relative bg-zinc-800/30 rounded-lg p-3 pr-12 border border-white/5 animate-slide-up"
            style={{ animationDelay: `${index * 100}ms` }}
          >
            {/* Number badge */}
            <span className="absolute top-3 left-3 w-5 h-5 flex items-center justify-center bg-white/10 rounded text-xs font-medium text-white/60">
              {index + 1}
            </span>

            {/* Suggestion text */}
            <p className="text-sm text-white/85 leading-relaxed pl-6">
              {suggestion}
            </p>

            {/* Copy button */}
            <button
              onClick={() => handleCopy(suggestion, index)}
              className="copy-btn absolute top-2 right-2 w-8 h-8 flex items-center justify-center rounded-md bg-white/5 hover:bg-white/10 transition-colors opacity-0 group-hover:opacity-100"
              title="Copy to clipboard"
            >
              {copiedIndex === index ? (
                <svg className="w-4 h-4 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                <svg className="w-4 h-4 text-white/60" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              )}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
