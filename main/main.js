const { app, BrowserWindow, ipcMain, dialog, nativeTheme } = require('electron');
const path = require('path');
const fs = require('fs');
const os = require('os');

const pythonHandlerPath = path.join(__dirname, 'modules', 'python-handler.js');
let pythonHandler;

try {
    pythonHandler = require(pythonHandlerPath);
    console.log('Módulo Python Handler cargado correctamente en el proceso principal');
} catch (error) {
    console.error('Error al cargar el módulo Python Handler:', error);
    // Implementación simulada en caso de error
    pythonHandler = {
        compilar: (code, runMode, callback) => {
            callback({
                error: 'No se pudo cargar el módulo Python Handler: ' + error.message
            });
        }
    };
}

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
    
    // Opcionalmente, abrir DevTools para depuración
    // win.webContents.openDevTools();
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

// Manejar la compilación de Python 
ipcMain.handle('python:compile', async (event, code, runMode) => {
    // Esta función convierte la API basada en callbacks a una Promise
    return new Promise((resolve, reject) => {
        try {
            pythonHandler.compilar(code, runMode, (result) => {
                if (result.error) {
                    // Devolvemos el error como un objeto estructurado, no como una excepción
                    resolve({ 
                        success: false, 
                        error: result.error, 
                        raw: result.raw || null 
                    });
                } else {
                    resolve({ 
                        success: true, 
                        ...result 
                    });
                }
            });
        } catch (error) {
            // Si hay una excepción en el proceso, la devolvemos estructurada
            resolve({ 
                success: false, 
                error: `Error al ejecutar el compilador: ${error.message}` 
            });
        }
    });
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