const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('darkMode', {
    toggle: () => ipcRenderer.invoke('dark-mode:toggle'),
});

contextBridge.exposeInMainWorld('fileAPI', {
    openFile: () => ipcRenderer.invoke('dialog:openFile'),
    saveFile: (content, filePath) => ipcRenderer.invoke('dialog:saveFile', content, filePath),
    saveFileAs: (content) => ipcRenderer.invoke('dialog:saveFileAs', content),
});

// Exponer require si es necesario
contextBridge.exposeInMainWorld('nodeAPI', {
    require: (module) => require(module),
});