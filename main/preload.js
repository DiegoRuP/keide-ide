const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('darkMode', {
    toggle: () => ipcRenderer.invoke('dark-mode:toggle'),
});

contextBridge.exposeInMainWorld('fileAPI', {
    openFile: () => ipcRenderer.invoke('dialog:openFile'),
    saveFile: (content, filePath) => ipcRenderer.invoke('dialog:saveFile', content, filePath),
    saveFileAs: (content) => ipcRenderer.invoke('dialog:saveFileAs', content),
});

contextBridge.exposeInMainWorld('nodeAPI', {
    require: (module) => require(module),
});

contextBridge.exposeInMainWorld('compilerAPI', {
    compile: (code, runMode) => ipcRenderer.invoke('python:compile', code, runMode),
});