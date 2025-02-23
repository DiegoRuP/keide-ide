const { app, BrowserWindow, ipcMain, dialog, nativeTheme } = require('electron'); // Importa nativeTheme
const path = require('path');
const fs = require('fs');
const fsPromises = fs.promises;

function createWindow() {
    const win = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: false,
            contextIsolation: true,
        },
    });

    win.loadFile(path.join(__dirname, '../renderer/index.html'));
}

// Manejar el cambio de tema oscuro/claro
ipcMain.handle('dark-mode:toggle', () => {
    if (nativeTheme.shouldUseDarkColors) {
        nativeTheme.themeSource = 'light'; // Cambiar a tema claro
    } else {
        nativeTheme.themeSource = 'dark'; // Cambiar a tema oscuro
    }
    return nativeTheme.shouldUseDarkColors; // Devolver el estado actual del tema
});

// Manejar la apertura de archivos
ipcMain.handle('dialog:openFile', async () => {
    const { filePaths } = await dialog.showOpenDialog({
        properties: ['openFile'],
        filters: [{ name: 'Text Files', extensions: ['txt', 'js', 'html', 'css', 'py'] }],
    });

    if (filePaths && filePaths.length > 0) {
        const filePath = filePaths[0];
        const content = fs.readFileSync(filePath, 'utf-8');
        return { filePath, content };
    }
    return null;
});

// Manejar el guardado de archivos
ipcMain.handle('dialog:saveFile', async (event, content, filePath) => {
    if (!filePath) {
        const { filePath: newFilePath } = await dialog.showSaveDialog({
            filters: [{ name: 'Text Files', extensions: ['txt', 'js', 'html', 'css', 'py'] }],
        });
        if (newFilePath) {
            fs.writeFileSync(newFilePath, content);
            return newFilePath;
        }
    } else {
        fs.writeFileSync(filePath, content);
        return filePath;
    }
    return null;
});

// Manejar "Guardar como"
ipcMain.handle('dialog:saveFileAs', async (event, content) => {
    const { filePath } = await dialog.showSaveDialog({
        filters: [{ name: 'Text Files', extensions: ['txt', 'js', 'html', 'css', 'py'] }],
    });
    if (filePath) {
        fs.writeFileSync(filePath, content);
        return filePath;
    }
    return null;
});

app.whenReady().then(() => {
    createWindow();

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