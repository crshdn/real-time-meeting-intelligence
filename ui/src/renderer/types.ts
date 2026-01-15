// Message types from backend WebSocket
export interface TranscriptMessage {
  type: 'transcript';
  text: string;
  speaker: 'prospect' | 'salesperson' | 'unknown';
  is_final: boolean;
}

export interface SuggestionsMessage {
  type: 'suggestions';
  items: string[];
}

export interface StatusMessage {
  type: 'status';
  listening: boolean;
  connected: boolean;
  transcribing: boolean;
}

export interface AckMessage {
  type: 'ack';
  success: boolean;
}

export interface ErrorMessage {
  type: 'error';
  message: string;
}

export type ServerMessage =
  | TranscriptMessage
  | SuggestionsMessage
  | StatusMessage
  | AckMessage
  | ErrorMessage;

// Client commands
export interface StartListeningCommand {
  type: 'start_listening';
}

export interface StopListeningCommand {
  type: 'stop_listening';
}

export interface GetStatusCommand {
  type: 'get_status';
}

export type ClientCommand =
  | StartListeningCommand
  | StopListeningCommand
  | GetStatusCommand;

// App state
export interface AppState {
  isConnected: boolean;
  isListening: boolean;
  isTranscribing: boolean;
  currentTranscript: string;
  currentSpeaker: string;
  suggestions: string[];
}
