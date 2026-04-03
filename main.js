const { app, BrowserWindow, screen, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process'); // Changed fork to spawn


const isDev = require('electron-is-dev');
const { autoUpdater } = require('electron-updater');

let mainWindow;
let backendProcess;

// Auto-updater configuration
autoUpdater.autoDownload = true;
autoUpdater.autoInstallOnAppQuit = true;

autoUpdater.on('checking-for-update', () => {
    console.log('Checking for update...');
});

autoUpdater.on('update-available', (info) => {
    console.log('Update available:', info.version);
    if (mainWindow) {
        mainWindow.webContents.send('update-available', info);
    }
});

autoUpdater.on('update-not-available', (info) => {
    console.log('Update not available. Current version:', info.version);
});

autoUpdater.on('error', (err) => {
    console.error('Update error:', err);
    if (mainWindow) {
        mainWindow.webContents.send('update-error', err);
    }
});

autoUpdater.on('download-progress', (progressObj) => {
    let log_message = "Download speed: " + progressObj.bytesPerSecond;
    log_message = log_message + ' - Downloaded ' + progressObj.percent + '%';
    log_message = log_message + ' (' + progressObj.transferred + "/" + progressObj.total + ')';
    console.log(log_message);
});

autoUpdater.on('update-downloaded', (info) => {
    console.log('Update downloaded:', info.version);
    if (mainWindow) {
        mainWindow.webContents.send('update-downloaded', info);
    }
    // Auto-install on quit is enabled, but you can also prompt user here
    // autoUpdater.quitAndInstall();
});

// IPC handlers for update actions
ipcMain.on('download-update', () => {
    autoUpdater.downloadUpdate();
});

ipcMain.on('restart-app', () => {
    autoUpdater.quitAndInstall();
});

function createWindow() {
    const { width, height } = screen.getPrimaryDisplay().workAreaSize;

    mainWindow = new BrowserWindow({
        width: width,
        height: height,
        frame: false, // Frameless for that futuristic look
        transparent: true, // Allow transparency if the HTML supports it
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            webSecurity: true
        },
        backgroundColor: '#000000' // Fallback background
    });

    // Handle permission requests (camera, microphone)
    mainWindow.webContents.session.setPermissionRequestHandler((webContents, permission, callback) => {
        const allowedPermissions = ['media', 'audioCapture', 'videoCapture', 'geolocation', 'notifications'];
        if (allowedPermissions.includes(permission)) {
            callback(true); // Approve permission request
        } else {
            callback(false); // Deny
        }
    });

    // Load the dashboard
    mainWindow.loadFile(path.join(__dirname, 'friday_app.html'));

    // Open DevTools in development mode
    if (isDev) {
        mainWindow.webContents.openDevTools({ mode: 'detach' });
    }

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

function startBackend() {
    const backendScript = path.join(__dirname, 'python_backend', 'main.py');
    console.log('Starting Python backend from:', backendScript);

    // Spawn the Python backend process
    backendProcess = spawn('python', [backendScript], {
        env: { ...process.env, PYTHONUNBUFFERED: '1' },
        stdio: 'inherit',
        cwd: __dirname
    });

    backendProcess.on('error', (err) => {
        console.error('Backend failed to start:', err);
    });

    backendProcess.on('exit', (code, signal) => {
        console.log(`Backend process exited with code ${code} and signal ${signal}`);
        if (code !== 0 && code !== null && code !== 1) {
            console.log('Backend exited. Restarting in 3s...');
            setTimeout(startBackend, 3000);
        }
    });
}

app.on('ready', () => {
    startBackend(); // AUTO-START: Re-enabled with Single-Instance Safety
    // Check for updates (only in production mode and if updates are configured)
    if (!isDev && autoUpdater.app && autoUpdater.app.isPackaged) {
        // Only check for updates if publish config exists
        try {
            autoUpdater.checkForUpdatesAndNotify();
        } catch (error) {
            console.log('Auto-updates not configured or unavailable');
        }
    }
    // Give the backend a moment to spin up before showing the window,
    // or just show it immediately and let the UI retry connections.
    setTimeout(createWindow, 1000);
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (mainWindow === null) {
        createWindow();
    }
});

app.on('will-quit', () => {
    // Kill the backend process when the app quits
    if (backendProcess) {
        backendProcess.kill();
    }
});
