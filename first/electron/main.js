const { app, BrowserWindow, Menu, ipcMain } = require('electron');
const path = require('path');
const isDev = require('electron-is-dev');
const { spawn } = require('child_process');
const fs = require('fs');

let mainWindow;
let pythonProcess = null;
const PORT = 3001;

// 로그 함수
function log(message) {
  console.log(`[Electron] ${new Date().toLocaleTimeString()} - ${message}`);
}

// Python 프로세스 시작
function startPythonBackend() {
  log('Python 백엔드 시작 중...');
  
  const pythonPath = process.env.PYTHON_PATH || 'python';
  const scriptPath = path.join(__dirname, 'backend', 'server.py');
  
  try {
    pythonProcess = spawn(pythonPath, [scriptPath, '--port', PORT.toString()], {
      stdio: ['ignore', 'pipe', 'pipe'],
      shell: process.platform === 'win32',
      detached: false
    });

    pythonProcess.stdout.on('data', (data) => {
      log(`[Python] ${data.toString().trim()}`);
    });

    pythonProcess.stderr.on('data', (data) => {
      const message = data.toString().trim();
      // INFO와 DEBUG 메시지는 정보 로그로, ERROR와 WARNING은 에러 로그로 표시
      if (message.includes('ERROR') || message.includes('Exception') || message.includes('Traceback')) {
        log(`[⚠️ Python Error] ${message}`);
      } else if (message.includes('INFO') || message.includes('werkzeug')) {
        log(`[ℹ️ Info] ${message}`);
      } else if (message.includes('WARNING')) {
        log(`[⚡ Warning] ${message}`);
      } else {
        log(`[Python] ${message}`);
      }
    });

    pythonProcess.on('error', (error) => {
      log(`Python 시작 오류: ${error.message}`);
    });

    pythonProcess.on('exit', (code) => {
      if (code !== 0) {
        log(`Python 프로세스 종료 (코드: ${code})`);
      }
    });

    log('Python 백엔드 시작 완료');
  } catch (error) {
    log(`Python 프로세스 시작 실패: ${error.message}`);
    throw error;
  }
}

// Python 프로세스 종료
function stopPythonBackend() {
  if (pythonProcess) {
    log('Python 백엔드 종료 중...');
    try {
      if (process.platform === 'win32') {
        spawn('taskkill', ['/pid', pythonProcess.pid, '/f']);
      } else {
        pythonProcess.kill('SIGTERM');
      }
      pythonProcess = null;
    } catch (error) {
      log(`Python 종료 오류: ${error.message}`);
    }
  }
}

// 메인 윈도우 생성
function createWindow() {
  log('메인 윈도우 생성 중...');
  
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js'),
      sandbox: true,
      disableHtmlCache: true,
      cache: false
    },
    icon: path.join(__dirname, 'assets', 'icon.ico'),
    show: false // 준비될 때까지 보이지 않음
  });

  // 캐시 완전히 비우기
  mainWindow.webContents.session.clearCache().then(() => {
    log('캐시 삭제 완료');
  });

  // 개발 모드에서는 캐시 비활성화
  mainWindow.webContents.session.clearStorageData({
    storages: ['appcache', 'filesystem', 'indexdb', 'localstorage', 'shadercache', 'websql', 'serviceworkers', 'cachestorage']
  });

  mainWindow.loadURL(`http://localhost:${PORT}`);

  // 윈도우가 준비되면 표시
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    log('윈도우 표시됨');
  });

  // 개발자 도구는 메뉴나 F12로만 열 수 있도록 변경
  // if (isDev) {
  //   mainWindow.webContents.openDevTools();
  //   log('개발 모드 (개발자 도구 열림)');
  // }

  mainWindow.on('closed', () => {
    mainWindow = null;
    log('메인 윈도우 종료됨');
  });

  log('메인 윈도우 생성 완료');
}

// 앱 이벤트
app.on('ready', () => {
  log('Electron 앱 시작');
  
  try {
    startPythonBackend();
    
    // Python 서버 시작 대기
    setTimeout(() => {
      createWindow();
    }, 3000);
  } catch (error) {
    log(`앱 시작 오류: ${error.message}`);
    app.quit();
  }
});

app.on('window-all-closed', () => {
  log('모든 윈도우 종료됨');
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

// 앱 종료 시 Python 프로세스 종료
app.on('before-quit', () => {
  log('앱 종료 중...');
  stopPythonBackend();
});

// IPC 통신
ipcMain.on('app-version', (event) => {
  event.reply('app-version', { 
    version: app.getVersion(),
    platform: process.platform
  });
});

ipcMain.handle('python-log', async (event, message) => {
  log(`[Renderer] ${message}`);
});

// 클리핑 창 생성
let clippingWindow = null;

function createClippingWindow() {
  if (clippingWindow) {
    clippingWindow.focus();
    return;
  }

  clippingWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js'),
      sandbox: true,
      disableHtmlCache: true
    },
    parent: mainWindow,
    modal: true,
    icon: path.join(__dirname, 'assets', 'icon.ico')
  });

  clippingWindow.loadURL(`http://localhost:${PORT}/clipping`);

  clippingWindow.once('ready-to-show', () => {
    clippingWindow.show();
    log('클리핑 설정 창 표시됨');
  });

  clippingWindow.on('closed', () => {
    clippingWindow = null;
    log('클리핑 설정 창 종료됨');
  });
}

// 메뉴
const template = [
  {
    label: '파일',
    submenu: [
      {
        label: '종료',
        accelerator: 'CmdOrCtrl+Q',
        click: () => {
          app.quit();
        }
      }
    ]
  },
  {
    label: '보기',
    submenu: [
      {
        label: '새로고침',
        accelerator: 'CmdOrCtrl+R',
        click: () => {
          if (mainWindow) mainWindow.reload();
        }
      },
      {
        label: '개발자 도구',
        accelerator: 'CmdOrCtrl+Shift+I',
        click: () => {
          if (mainWindow) mainWindow.webContents.openDevTools();
        }
      }
    ]
  },
  {
    label: '정보',
    submenu: [
      {
        label: '버전 정보',
        click: () => {
          if (mainWindow) {
            mainWindow.webContents.executeJavaScript(`
              alert('구글&네이버 뉴스 크롤러\\nElectron 버전 2.0\\nNode: ${process.versions.node}');
            `);
          }
        }
      }
    ]
  }
];

const menu = Menu.buildFromTemplate(template);
Menu.setApplicationMenu(menu);

log('Electron 앱 초기화 완료');
