import { app, BrowserWindow, screen, ipcMain, Tray, Menu, nativeImage } from 'electron';
import * as path from 'path';

let mainWindow: BrowserWindow | null = null;
let tray: Tray | null = null;

const isDev = process.env.NODE_ENV !== 'production' || !app.isPackaged;

function createWindow(): void {
  // Get primary display dimensions
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width: screenWidth, height: screenHeight } = primaryDisplay.workAreaSize;

  // Window dimensions
  const windowWidth = 400;
  const windowHeight = 500;

  // Position in bottom-right corner with padding
  const x = screenWidth - windowWidth - 20;
  const y = screenHeight - windowHeight - 20;

  mainWindow = new BrowserWindow({
    width: windowWidth,
    height: windowHeight,
    x,
    y,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    resizable: true,
    minimizable: true,
    maximizable: false,
    skipTaskbar: false,
    hasShadow: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
      webSecurity: true,
    },
  });

  // Set minimum size
  mainWindow.setMinimumSize(350, 400);

  // Load the app
  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
    // Open DevTools in development
    mainWindow.webContents.openDevTools({ mode: 'detach' });
  } else {
    mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'));
  }

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Keep window on top even when losing focus
  mainWindow.on('blur', () => {
    if (mainWindow && mainWindow.isAlwaysOnTop()) {
      mainWindow.setAlwaysOnTop(true, 'floating');
    }
  });
}

function createTray(): void {
  // Create a simple tray icon (1x1 transparent for now, will be replaced)
  const icon = nativeImage.createEmpty();

  tray = new Tray(icon);
  tray.setToolTip('Sales Assistant');

  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show/Hide',
      click: () => {
        if (mainWindow) {
          if (mainWindow.isVisible()) {
            mainWindow.hide();
          } else {
            mainWindow.show();
            mainWindow.focus();
          }
        }
      },
    },
    {
      label: 'Always on Top',
      type: 'checkbox',
      checked: true,
      click: (menuItem) => {
        if (mainWindow) {
          mainWindow.setAlwaysOnTop(menuItem.checked);
        }
      },
    },
    { type: 'separator' },
    {
      label: 'Quit',
      click: () => {
        app.quit();
      },
    },
  ]);

  tray.setContextMenu(contextMenu);

  // Show window on tray click
  tray.on('click', () => {
    if (mainWindow) {
      mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show();
    }
  });
}

// IPC handlers
function setupIPC(): void {
  // Window controls
  ipcMain.handle('window:minimize', () => {
    mainWindow?.minimize();
  });

  ipcMain.handle('window:close', () => {
    mainWindow?.hide();
  });

  ipcMain.handle('window:toggle-always-on-top', () => {
    if (mainWindow) {
      const current = mainWindow.isAlwaysOnTop();
      mainWindow.setAlwaysOnTop(!current);
      return !current;
    }
    return true;
  });

  // Clipboard
  ipcMain.handle('clipboard:write', (_event, text: string) => {
    const { clipboard } = require('electron');
    clipboard.writeText(text);
    return true;
  });
}

// App lifecycle
app.whenReady().then(() => {
  setupIPC();
  createWindow();
  createTray();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  if (tray) {
    tray.destroy();
    tray = null;
  }
});
