const { contextBridge, ipcRenderer, clipboard } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  getVersion: () => ipcRenderer.invoke('app-version'),
  onAppVersion: (callback) => ipcRenderer.on('app-version', callback),
  send: (channel, data) => {
    ipcRenderer.send(channel, data);
  },
  clipboard: {
    writeText: (text) => clipboard.writeText(text),
    readText: () => clipboard.readText()
  }
});
