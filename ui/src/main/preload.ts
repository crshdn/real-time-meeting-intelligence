import { contextBridge, ipcRenderer } from 'electron';

// Expose protected methods to the renderer process
contextBridge.exposeInMainWorld('electronAPI', {
  // Window controls
  minimize: () => ipcRenderer.invoke('window:minimize'),
  close: () => ipcRenderer.invoke('window:close'),
  toggleAlwaysOnTop: () => ipcRenderer.invoke('window:toggle-always-on-top'),

  // Clipboard
  copyToClipboard: (text: string) => ipcRenderer.invoke('clipboard:write', text),
});

// Type declarations for the exposed API
declare global {
  interface Window {
    electronAPI: {
      minimize: () => Promise<void>;
      close: () => Promise<void>;
      toggleAlwaysOnTop: () => Promise<boolean>;
      copyToClipboard: (text: string) => Promise<boolean>;
    };
  }
}
