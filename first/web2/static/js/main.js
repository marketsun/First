// ============================================================
// 구글&네이버 뉴스 크롤러 - 메인 JavaScript
// 상세 로그 시스템 포함
// ============================================================

// ========== DOM Elements ==========
const keywordInputToolbar = document.getElementById('keyword-input-toolbar');
const crawlBtnToolbar = document.getElementById('crawl-btn-toolbar');
const googleNewsTableBody = document.getElementById('google-news-table-body');
const naverNewsTableBody = document.getElementById('naver-news-table-body');
const selectionTableBody = document.getElementById('selection-table-body');
const googleCount = document.getElementById('google-count');
const naverCount = document.getElementById('naver-count');
const selectionCount = document.getElementById('selection-count');
const googleEmptyState = document.getElementById('google-empty-state');
const naverEmptyState = document.getElementById('naver-empty-state');
const selectionEmpty = document.getElementById('selection-empty');
const logContainer = document.getElementById('log-container');
const logToggleBtn = document.getElementById('log-toggle-btn');
const logFloatingPanel = document.getElementById('log-floating-panel');
const closeLogBtn = document.getElementById('close-log-btn');
const clearLogBtnFloat = document.getElementById('clear-log-btn-float');
const copyRecentLogBtn = document.getElementById('copy-recent-log-btn');
const copyAllLogBtn = document.getElementById('copy-all-log-btn');
const customLogLinesInput = document.getElementById('custom-log-lines');
const logStatusSpan = document.getElementById('log-status');
const copySelectionBtn = document.getElementById('copy-selection-btn');
const clearAllSelectionBtn = document.getElementById('clear-all-selection-btn');

// ========== Global Variables ==========
let selectedNews = [];
let allNewsData = [];
let allNaverNewsData = [];

// ========== Logging System (최적화) ==========
// 로그를 메모리에만 저장 (DOM 조작 최소화)
const logMemory = [];
const MAX_LOGS = 5000; // 메모리에는 5000줄까지 저장
let logRenderTimeout = null;
let isLogPanelOpen = false;

/**
 * 로그 추가 함수 (메모리 기반, 성능 최적화)
 * @param {string} message - 로그 메시지
 * @param {string} type - 로그 타입 (info, debug, success, warning, error, system, data, branch, loop, api, dom)
 */
function addLog(message, type = 'info') {
    const timeStr = new Date().toLocaleTimeString('ko-KR', { 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit',
        fractionalSecondDigits: 3 
    });
    
    // 메모리에만 저장 (DOM 조작 없음)
    logMemory.push({
        time: timeStr,
        message: message,
        type: type,
        timestamp: Date.now()
    });
    
    // 메모리 제한 (FIFO)
    if (logMemory.length > MAX_LOGS) {
        logMemory.shift();
    }
    
    // 로그 패널이 열려있을 때만 렌더링 (디바운싱)
    if (isLogPanelOpen) {
        scheduleLogRender();
    }
}

/**
 * 로그 렌더링 스케줄링 (디바운싱)
 */
function scheduleLogRender() {
    if (logRenderTimeout) {
        clearTimeout(logRenderTimeout);
    }
    
    // 100ms 후에 렌더링 (여러 로그가 동시에 추가되어도 한 번만 렌더링)
    logRenderTimeout = setTimeout(() => {
        renderLogs();
    }, 100);
}

/**
 * 로그 렌더링 (마지막 200줄만)
 */
function renderLogs() {
    if (!logContainer) return;
    
    // 마지막 200줄만 렌더링
    const logsToRender = logMemory.slice(-200);
    
    // DocumentFragment 사용으로 DOM 조작 최소화
    const fragment = document.createDocumentFragment();
    
    logsToRender.forEach(log => {
        const logItem = document.createElement('div');
        logItem.className = `log-item ${log.type}`;
        logItem.textContent = `[${log.time}] ${log.message}`;
        fragment.appendChild(logItem);
    });
    
    // 한 번에 DOM 업데이트
    logContainer.innerHTML = '';
    logContainer.appendChild(fragment);
    logContainer.scrollTop = logContainer.scrollHeight;
    
    // 상태 업데이트
    updateLogStatus();
}

/**
 * 로그 상태 업데이트
 */
function updateLogStatus() {
    if (!logStatusSpan) return;
    
    const count = logMemory.length;
    const displayCount = Math.min(count, 200);
    const percentage = Math.round((count / MAX_LOGS) * 100);
    
    logStatusSpan.textContent = `${count}/${MAX_LOGS} 줄 저장됨 (화면: ${displayCount}줄)`;
    
    // 경고 색상
    if (count > 4000) {
        logStatusSpan.style.color = '#D92D20';
    } else if (count > 3000) {
        logStatusSpan.style.color = '#F79009';
    } else {
        logStatusSpan.style.color = '#4E5968';
    }
}

/**
 * 최근 N줄 로그 복사 (메모리 기반)
 * @param {number} lines - 복사할 줄 수
 */
function copyRecentLogs(lines = 200) {
    console.log('[DEBUG] copyRecentLogs 호출됨, lines =', lines);
    
    try {
        // 메모리에서 직접 가져오기 (DOM 조작 없음)
        const recentLogs = logMemory.slice(-lines);
        console.log('[DEBUG] 복사할 로그 수:', recentLogs.length);
        
        const text = recentLogs.map(log => `[${log.time}] ${log.message}`).join('\n');
        console.log('[DEBUG] 복사할 텍스트 길이:', text.length);
        
        // Electron clipboard API 사용 (우선순위)
        if (window.electronAPI && window.electronAPI.clipboard) {
            console.log('[DEBUG] Electron clipboard API 사용');
            window.electronAPI.clipboard.writeText(text);
        } else {
            console.log('[DEBUG] 브라우저 clipboard API 사용');
            navigator.clipboard.writeText(text).then(() => {
                console.log('[DEBUG] 브라우저 clipboard 복사 성공');
            }).catch(err => {
                console.error('[DEBUG] 브라우저 clipboard 복사 실패:', err);
                throw err;
            });
        }
        
        console.log('[DEBUG] copyRecentLogs 완료');
        alert(`✅ 최근 ${recentLogs.length}줄 복사 완료 (${text.length} 문자)`);
    } catch (error) {
        console.error('[DEBUG] copyRecentLogs 에러:', error);
        alert('복사 실패: ' + error.message);
    }
}

/**
 * 전체 로그 복사 (메모리 기반)
 */
function copyAllLogs() {
    console.log('='.repeat(50));
    console.log('[DEBUG] copyAllLogs 호출됨');
    
    try {
        // 메모리에서 직접 가져오기
        const text = logMemory.map(log => `[${log.time}] ${log.message}`).join('\n');
        console.log('[DEBUG] 전체 로그 수:', logMemory.length);
        console.log('[DEBUG] 복사할 텍스트 길이:', text.length);
        
        // Electron clipboard API 사용 (우선순위)
        if (window.electronAPI && window.electronAPI.clipboard) {
            console.log('[DEBUG] Electron clipboard API 사용');
            window.electronAPI.clipboard.writeText(text);
        } else {
            console.log('[DEBUG] 브라우저 clipboard API 사용');
            navigator.clipboard.writeText(text).then(() => {
                console.log('[DEBUG] 브라우저 clipboard 복사 성공');
            }).catch(err => {
                console.error('[DEBUG] 브라우저 clipboard 복사 실패:', err);
                throw err;
            });
        }
        
        console.log('[DEBUG] copyAllLogs 완료');
        alert(`✅ 전체 ${logMemory.length}줄 복사 완료 (${text.length} 문자)`);
    } catch (error) {
        console.error('[DEBUG] copyAllLogs 에러:', error);
        alert('복사 실패: ' + error.message);
    }
}

/**
 * 로그 전체 삭제 (메모리 기반)
 */
function clearAllLogs() {
    const count = logMemory.length;
    
    // 메모리 초기화
    logMemory.length = 0;
    
    // DOM 초기화
    if (logContainer) {
        logContainer.innerHTML = '';
    }
    
    updateLogStatus();
    alert(`✅ ${count}줄 로그 삭제 완료`);
}

// ========== API Functions ==========
/**
 * 뉴스 크롤링 API 호출
 */
async function crawlNews() {
    addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
    addLog('[함수호출] crawlNews()', 'debug');
    
    // 키워드 확인
    addLog('├─ [DOM확인] keywordInputToolbar 존재 여부', 'dom');
    if (!keywordInputToolbar) {
        addLog('│  └─ [에러] keywordInputToolbar = null', 'error');
        addLog('[함수종료] crawlNews() - 실패', 'debug');
        addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
        return;
    }
    addLog('│  └─ [성공] keywordInputToolbar = <input>', 'dom');
    
    const keyword = keywordInputToolbar.value?.trim();
    addLog(`├─ [변수] keyword = "${keyword}"`, 'data');
    
    // 조건 분기: 키워드 존재 여부
    if (!keyword) {
        addLog('├─ [조건분기] keyword 없음 → 경고 출력 후 종료', 'branch');
        addLog('[함수종료] crawlNews() - 키워드 없음', 'debug');
        addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
        addLog('⚠️ 검색어를 입력하세요', 'warning');
        return;
    }
    addLog('├─ [조건분기] keyword 있음 → 검색 진행', 'branch');
    
    try {
        // 로딩 상태 표시
        const googleLoadingState = document.getElementById('google-loading-state');
        const naverLoadingState = document.getElementById('naver-loading-state');
        const googleEmptyState = document.getElementById('google-empty-state');
        const naverEmptyState = document.getElementById('naver-empty-state');
        
        if (googleLoadingState) googleLoadingState.style.display = 'flex';
        if (naverLoadingState) naverLoadingState.style.display = 'flex';
        if (googleEmptyState) googleEmptyState.style.display = 'none';
        if (naverEmptyState) naverEmptyState.style.display = 'none';
        
        addLog(`├─ [API호출] POST /api/crawl`, 'api');
        addLog(`│  ├─ [요청메소드] POST`, 'api');
        addLog(`│  ├─ [요청헤더] Content-Type: application/json`, 'api');
        addLog(`│  ├─ [요청바디] ${JSON.stringify({ keyword: keyword })}`, 'api');
        addLog(`│  └─ [상태] 요청 전송 중...`, 'api');
        
        addLog(`🔍 "${keyword}" 검색 중...`, 'info');
        
        const startTime = performance.now();
        const response = await fetch('/api/crawl', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ keyword: keyword })
        });
        const endTime = performance.now();
        const duration = ((endTime - startTime) / 1000).toFixed(2);
        
        // 로딩 상태 숨기기
        if (googleLoadingState) googleLoadingState.style.display = 'none';
        if (naverLoadingState) naverLoadingState.style.display = 'none';
        
        addLog(`│  ├─ [응답수신] ${response.status} ${response.statusText}`, 'api');
        addLog(`│  ├─ [소요시간] ${duration}초`, 'api');
        
        if (!response.ok) {
            addLog(`│  └─ [에러] HTTP 상태 코드 ${response.status}`, 'error');
            throw new Error(`HTTP ${response.status}`);
        }
        
        const result = await response.json();
        addLog(`│  ├─ [응답파싱] JSON 파싱 완료`, 'api');
        addLog(`│  ├─ [응답데이터] success = ${result.success}`, 'api');
        addLog(`│  ├─ [응답데이터] google_news.length = ${result.google_news?.length || 0}`, 'api');
        addLog(`│  └─ [응답데이터] naver_news.length = ${result.naver_news?.length || 0}`, 'api');
        
        // 조건 분기: 성공 여부
        if (result.success) {
            addLog('├─ [조건분기] result.success = true → 데이터 처리', 'branch');
            
            allNewsData = result.google_news || [];
            addLog(`├─ [변수할당] allNewsData = [${allNewsData.length}개 배열]`, 'data');
            
            // 구글 뉴스 렌더링
            addLog('├─ [함수호출] renderNewsTable(allNewsData)', 'debug');
            renderNewsTable(allNewsData);
            
            // 네이버 뉴스 크롤링 시작
            addLog('├─ [API호출] POST /api/crawl/naver 시작', 'api');
            fetch('/api/crawl/naver', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ keyword: keyword })
            })
            .then(res => res.json())
            .then(naverResult => {
                addLog('│  ├─ [API응답] 네이버 크롤링 완료', 'api');
                addLog(`│  └─ [응답데이터] news.length = ${naverResult.news?.length || 0}`, 'api');
                
                allNaverNewsData = naverResult.news || [];
                addLog(`├─ [변수할당] allNaverNewsData = [${allNaverNewsData.length}개 배열]`, 'data');
                
                // 네이버 뉴스 렌더링
                addLog('├─ [함수호출] renderNaverNewsTable(allNaverNewsData)', 'debug');
                renderNaverNewsTable(allNaverNewsData);
                
                addLog('[함수종료] crawlNews() - 성공', 'debug');
                addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
                addLog(`✅ 검색 완료: 구글 ${allNewsData.length}개, 네이버 ${allNaverNewsData.length}개`, 'success');
            })
            .catch(error => {
                addLog(`├─ [예외발생] 네이버 크롤링 오류: ${error.message}`, 'error');
                renderNaverNewsTable([]);
            });
        } else {
            addLog('├─ [조건분기] result.success = false → 검색 실패', 'branch');
            addLog('[함수종료] crawlNews() - 실패', 'debug');
            addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
            addLog('❌ 검색 실패', 'error');
        }
    } catch (error) {
        addLog(`├─ [예외발생] ${error.name}: ${error.message}`, 'error');
        addLog(`├─ [스택트레이스] ${error.stack}`, 'error');
        addLog('[함수종료] crawlNews() - 예외 발생', 'debug');
        addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
        addLog(`❌ 오류: ${error.message}`, 'error');
    }
}

/**
 * 구글 뉴스 테이블 렌더링
 * @param {Array} newsList - 뉴스 배열
 */
function renderNewsTable(newsList) {
    addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
    addLog('[함수호출] renderNewsTable()', 'debug');
    addLog(`├─ [파라미터] newsList.length = ${newsList?.length || 'null'}`, 'debug');
    
    // DOM 확인
    addLog('├─ [DOM확인] googleNewsTableBody 존재 여부', 'dom');
    if (!googleNewsTableBody) {
        addLog('│  └─ [에러] googleNewsTableBody = null', 'error');
        addLog('[함수종료] renderNewsTable() - 실패', 'debug');
        addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
        return;
    }
    addLog('│  └─ [성공] googleNewsTableBody = <tbody>', 'dom');
    
    // 테이블 초기화
    googleNewsTableBody.innerHTML = '';
    addLog('├─ [DOM조작] googleNewsTableBody.innerHTML = ""', 'dom');
    
    // 카운트 업데이트
    if (googleCount) {
        googleCount.textContent = newsList.length;
        addLog(`├─ [DOM조작] googleCount.textContent = ${newsList.length}`, 'dom');
    }
    
    // 조건 분기: 빈 목록
    if (newsList.length === 0) {
        addLog('├─ [조건분기] newsList.length = 0 → 빈 상태 표시', 'branch');
        if (googleEmptyState) {
            googleEmptyState.style.display = 'block';
            addLog('├─ [DOM조작] googleEmptyState.style.display = "block"', 'dom');
        }
        addLog('[함수종료] renderNewsTable() - 빈 목록', 'debug');
        addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
        return;
    }
    
    addLog('├─ [조건분기] newsList.length > 0 → 렌더링 진행', 'branch');
    
    // 빈 상태 숨김
    if (googleEmptyState) {
        googleEmptyState.style.display = 'none';
        addLog('├─ [DOM조작] googleEmptyState.style.display = "none"', 'dom');
    }
    
    // 반복문: 뉴스 렌더링
    addLog(`├─ [반복시작] forEach ${newsList.length}회`, 'loop');
    newsList.forEach((news, idx) => {
        const tr = document.createElement('tr');
        tr.dataset.newsId = news.id;
        
        // 선택 상태 확인
        const isSelected = selectedNews.some(n => n.id === news.id);
        if (isSelected) {
            tr.classList.add('selected');
        }
        
        // 로그 (처음 3개와 마지막만)
        if (idx < 3 || idx === newsList.length - 1) {
            addLog(`│  ├─ [반복중] ${idx + 1}/${newsList.length} - id=${news.id}, selected=${isSelected}`, 'loop');
        } else if (idx === 3) {
            addLog(`│  ├─ [반복중] ... (${newsList.length - 4}개 생략)`, 'loop');
        }
        
        tr.innerHTML = `
            <td>${news.published_time || '-'}</td>
            <td>${news.source || '-'}</td>
            <td>${news.title}</td>
            <td><button class="btn-open-news" onclick="window.open('${news.link}', '_blank')">열기</button></td>
        `;
        
        tr.addEventListener('click', (e) => {
            if (e.target.tagName !== 'BUTTON') {
                toggleSelection(news);
            }
        });
        
        googleNewsTableBody.appendChild(tr);
    });
    addLog('├─ [반복종료] 렌더링 완료', 'loop');
    
    addLog('[함수종료] renderNewsTable() - 성공', 'debug');
    addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
}

/**
 * 네이버 뉴스 테이블 렌더링
 * @param {Array} newsList - 뉴스 배열
 */
function renderNaverNewsTable(newsList) {
    addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
    addLog('[함수호출] renderNaverNewsTable()', 'debug');
    addLog(`├─ [파라미터] newsList.length = ${newsList?.length || 'null'}`, 'debug');
    
    // DOM 확인
    addLog('├─ [DOM확인] naverNewsTableBody 존재 여부', 'dom');
    if (!naverNewsTableBody) {
        addLog('│  └─ [에러] naverNewsTableBody = null', 'error');
        addLog('[함수종료] renderNaverNewsTable() - 실패', 'debug');
        addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
        return;
    }
    addLog('│  └─ [성공] naverNewsTableBody = <tbody>', 'dom');
    
    // 테이블 초기화
    naverNewsTableBody.innerHTML = '';
    addLog('├─ [DOM조작] naverNewsTableBody.innerHTML = ""', 'dom');
    
    // 카운트 업데이트
    if (naverCount) {
        naverCount.textContent = newsList.length;
        addLog(`├─ [DOM조작] naverCount.textContent = ${newsList.length}`, 'dom');
    }
    
    // 조건 분기: 빈 목록
    if (newsList.length === 0) {
        addLog('├─ [조건분기] newsList.length = 0 → 빈 상태 표시', 'branch');
        if (naverEmptyState) {
            naverEmptyState.style.display = 'block';
            addLog('├─ [DOM조작] naverEmptyState.style.display = "block"', 'dom');
        }
        addLog('[함수종료] renderNaverNewsTable() - 빈 목록', 'debug');
        addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
        return;
    }
    
    addLog('├─ [조건분기] newsList.length > 0 → 렌더링 진행', 'branch');
    
    // 빈 상태 숨김
    if (naverEmptyState) {
        naverEmptyState.style.display = 'none';
        addLog('├─ [DOM조작] naverEmptyState.style.display = "none"', 'dom');
    }
    
    // 반복문: 뉴스 렌더링
    addLog(`├─ [반복시작] forEach ${newsList.length}회`, 'loop');
    newsList.forEach((news, idx) => {
        const tr = document.createElement('tr');
        tr.dataset.newsId = news.id;
        
        // 선택 상태 확인
        const isSelected = selectedNews.some(n => n.id === news.id);
        if (isSelected) {
            tr.classList.add('selected');
        }
        
        // 로그 (처음 3개와 마지막만)
        if (idx < 3 || idx === newsList.length - 1) {
            addLog(`│  ├─ [반복중] ${idx + 1}/${newsList.length} - id=${news.id}, selected=${isSelected}`, 'loop');
        } else if (idx === 3) {
            addLog(`│  ├─ [반복중] ... (${newsList.length - 4}개 생략)`, 'loop');
        }
        
        tr.innerHTML = `
            <td>${news.published_time || '-'}</td>
            <td>${news.source || '-'}</td>
            <td>${news.title}</td>
            <td><button class="btn-open-news" onclick="window.open('${news.link}', '_blank')">열기</button></td>
        `;
        
        tr.addEventListener('click', (e) => {
            if (e.target.tagName !== 'BUTTON') {
                toggleSelection(news);
            }
        });
        
        naverNewsTableBody.appendChild(tr);
    });
    addLog('├─ [반복종료] 렌더링 완료', 'loop');
    
    addLog('[함수종료] renderNaverNewsTable() - 성공', 'debug');
    addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
}

/**
 * 선택한 기사 테이블 렌더링
 */
function renderSelectionTable() {
    addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
    addLog('[함수호출] renderSelectionTable()', 'debug');
    addLog(`├─ [변수] selectedNews.length = ${selectedNews.length}`, 'data');
    
    // DOM 확인
    addLog('├─ [DOM확인] selectionTableBody 존재 여부', 'dom');
    if (!selectionTableBody) {
        addLog('│  └─ [에러] selectionTableBody = null', 'error');
        addLog('[함수종료] renderSelectionTable() - 실패', 'debug');
        addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
        return;
    }
    addLog('│  └─ [성공] selectionTableBody = <tbody>', 'dom');
    
    // 테이블 초기화
    selectionTableBody.innerHTML = '';
    addLog('├─ [DOM조작] selectionTableBody.innerHTML = ""', 'dom');
    
    // 카운트 업데이트
    if (selectionCount) {
        selectionCount.textContent = selectedNews.length;
        addLog(`├─ [DOM조작] selectionCount.textContent = ${selectedNews.length}`, 'dom');
    }
    
    // 조건 분기: 빈 목록
    if (selectedNews.length === 0) {
        addLog('├─ [조건분기] selectedNews.length = 0 → 빈 상태 표시', 'branch');
        if (selectionEmpty) {
            selectionEmpty.style.display = 'block';
            addLog('├─ [DOM조작] selectionEmpty.style.display = "block"', 'dom');
        }
        addLog('[함수종료] renderSelectionTable() - 빈 목록', 'debug');
        addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
        return;
    }
    
    addLog('├─ [조건분기] selectedNews.length > 0 → 렌더링 진행', 'branch');
    
    // 빈 상태 숨김
    if (selectionEmpty) {
        selectionEmpty.style.display = 'none';
        addLog('├─ [DOM조작] selectionEmpty.style.display = "none"', 'dom');
    }
    
    // 반복문: 선택 기사 렌더링
    addLog(`├─ [반복시작] forEach ${selectedNews.length}회`, 'loop');
    selectedNews.forEach((news, idx) => {
        if (idx < 3 || idx === selectedNews.length - 1) {
            addLog(`│  ├─ [반복중] ${idx + 1}/${selectedNews.length} - id=${news.id}`, 'loop');
        } else if (idx === 3) {
            addLog(`│  ├─ [반복중] ... (${selectedNews.length - 4}개 생략)`, 'loop');
        }
        
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${news.published_time || '-'}</td>
            <td>${news.source || '-'}</td>
            <td>${news.title}</td>
            <td><button onclick="removeFromSelection(${news.id})">X</button></td>
        `;
        selectionTableBody.appendChild(tr);
    });
    addLog('├─ [반복종료] 렌더링 완료', 'loop');
    
    addLog('[함수종료] renderSelectionTable() - 성공', 'debug');
    addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
}

// ========== Selection Functions ==========
/**
 * 기사 선택/해제 토글
 * @param {Object} news - 뉴스 객체
 */
function toggleSelection(news) {
    addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
    addLog('[함수호출] toggleSelection()', 'debug');
    addLog(`├─ [파라미터] news.id = ${news.id}`, 'debug');
    addLog(`├─ [파라미터] news.title = "${news.title?.substring(0, 30)}..."`, 'debug');
    
    const index = selectedNews.findIndex(n => n.id === news.id);
    addLog(`├─ [변수] index = ${index}`, 'data');
    
    // 조건 분기: 이미 선택됨
    if (index > -1) {
        addLog('├─ [조건분기] index > -1 → 선택 해제', 'branch');
        selectedNews.splice(index, 1);
        addLog(`├─ [배열조작] selectedNews.splice(${index}, 1)`, 'data');
        addLog(`├─ [변수] selectedNews.length = ${selectedNews.length}`, 'data');
        addLog('├─ [함수호출] renderNewsTable(allNewsData)', 'debug');
        renderNewsTable(allNewsData);
        addLog('├─ [함수호출] renderNaverNewsTable(allNaverNewsData)', 'debug');
        renderNaverNewsTable(allNaverNewsData);
        addLog('├─ [함수호출] renderSelectionTable()', 'debug');
        renderSelectionTable();
        addLog('[함수종료] toggleSelection() - 선택 해제', 'debug');
        addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
        addLog(`ℹ️ 기사 선택 해제: ${news.title?.substring(0, 30)}...`, 'info');
    } else {
        addLog('├─ [조건분기] index === -1 → 선택 추가', 'branch');
        selectedNews.push(news);
        addLog(`├─ [배열조작] selectedNews.push(news)`, 'data');
        addLog(`├─ [변수] selectedNews.length = ${selectedNews.length}`, 'data');
        addLog('├─ [함수호출] renderNewsTable(allNewsData)', 'debug');
        renderNewsTable(allNewsData);
        addLog('├─ [함수호출] renderNaverNewsTable(allNaverNewsData)', 'debug');
        renderNaverNewsTable(allNaverNewsData);
        addLog('├─ [함수호출] renderSelectionTable()', 'debug');
        renderSelectionTable();
        addLog('[함수종료] toggleSelection() - 선택 추가', 'debug');
        addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
        addLog(`ℹ️ 기사 선택: ${news.title?.substring(0, 30)}...`, 'info');
    }
}

/**
 * 선택한 기사 테이블 렌더링
 */
function renderSelectedNews() {
    addLog('[함수호출] renderSelectedNews()', 'debug');
    addLog(`├─ [변수] selectedNews.length = ${selectedNews.length}`, 'data');
    
    const selectedTableBody = document.getElementById('selected-news-table-body');
    const selectedCountSpan = document.querySelector('#selected-news-section h3');
    
    if (!selectedTableBody) {
        addLog('├─ [에러] selected-news-table-body 없음', 'error');
        addLog('[함수종료] renderSelectedNews() - DOM 없음', 'debug');
        return;
    }
    
    // 카운트 업데이트
    if (selectedCountSpan) {
        selectedCountSpan.textContent = `선택한 기사 (${selectedNews.length})`;
        addLog(`├─ [DOM조작] 카운트 업데이트: ${selectedNews.length}`, 'dom');
    }
    
    // 테이블 비우기
    selectedTableBody.innerHTML = '';
    addLog('├─ [DOM조작] 테이블 초기화', 'dom');
    
    if (selectedNews.length === 0) {
        addLog('├─ [조건분기] selectedNews.length === 0 → 빈 상태', 'branch');
        addLog('[함수종료] renderSelectedNews() - 빈 상태', 'debug');
        return;
    }
    
    // 선택된 기사 렌더링
    addLog('├─ [반복시작] selectedNews 렌더링', 'loop');
    selectedNews.forEach((news, index) => {
        const tr = document.createElement('tr');
        tr.className = 'selected-news-row';
        
        tr.innerHTML = `
            <td class="news-time">${news.published_time || '-'}</td>
            <td class="news-source">${news.source || '-'}</td>
            <td class="news-title">${news.title}</td>
            <td class="news-action">
                <button class="btn-remove" data-news-id="${news.id}">X</button>
            </td>
        `;
        
        // 제거 버튼 이벤트
        const removeBtn = tr.querySelector('.btn-remove');
        removeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            removeFromSelection(news.id);
        });
        
        selectedTableBody.appendChild(tr);
    });
    addLog('├─ [반복종료] 렌더링 완료', 'loop');
    
    addLog('[함수종료] renderSelectedNews() - 성공', 'debug');
}

/**
 * 선택 목록에서 제거
 * @param {number} newsId - 뉴스 ID
 */
function removeFromSelection(newsId) {
    addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
    addLog('[함수호출] removeFromSelection()', 'debug');
    addLog(`├─ [파라미터] newsId = ${newsId}`, 'debug');
    
    const beforeLength = selectedNews.length;
    selectedNews = selectedNews.filter(n => n.id !== newsId);
    const afterLength = selectedNews.length;
    
    addLog(`├─ [배열조작] selectedNews.filter()`, 'data');
    addLog(`├─ [변수] 이전 길이 = ${beforeLength}, 이후 길이 = ${afterLength}`, 'data');
    
    addLog('├─ [함수호출] renderNewsTable(allNewsData)', 'debug');
    renderNewsTable(allNewsData);
    addLog('├─ [함수호출] renderNaverNewsTable(allNaverNewsData)', 'debug');
    renderNaverNewsTable(allNaverNewsData);
    addLog('├─ [함수호출] renderSelectionTable()', 'debug');
    renderSelectionTable();
    
    addLog('[함수종료] removeFromSelection() - 성공', 'debug');
    addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
    addLog(`ℹ️ 기사 제거 완료`, 'info');
}

/**
 * 전체 선택 해제
 */
function clearAllSelection() {
    addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
    addLog('[함수호출] clearAllSelection()', 'debug');
    
    const count = selectedNews.length;
    addLog(`├─ [변수] 해제할 기사 수 = ${count}`, 'data');
    
    selectedNews = [];
    addLog('├─ [배열조작] selectedNews = []', 'data');
    
    addLog('├─ [함수호출] renderNewsTable(allNewsData)', 'debug');
    renderNewsTable(allNewsData);
    addLog('├─ [함수호출] renderNaverNewsTable(allNaverNewsData)', 'debug');
    renderNaverNewsTable(allNaverNewsData);
    addLog('├─ [함수호출] renderSelectionTable()', 'debug');
    renderSelectionTable();
    
    addLog('[함수종료] clearAllSelection() - 성공', 'debug');
    addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
    addLog(`✅ ${count}개 기사 전체 선택 해제`, 'success');
}

/**
 * 선택한 기사 복사
 */
async function copySelectedNews() {
    addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
    addLog('[함수호출] copySelectedNews()', 'debug');
    addLog(`├─ [변수] selectedNews.length = ${selectedNews.length}`, 'data');
    
    // 조건 분기: 선택된 기사 없음
    if (selectedNews.length === 0) {
        addLog('├─ [조건분기] selectedNews.length = 0 → 경고 출력 후 종료', 'branch');
        addLog('[함수종료] copySelectedNews() - 선택 없음', 'debug');
        addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
        addLog('⚠️ 선택된 기사가 없습니다', 'warning');
        return;
    }
    
    addLog('├─ [조건분기] selectedNews.length > 0 → 복사 진행', 'branch');
    
    const text = selectedNews.map((n, i) => `${i + 1}. ${n.title}\n${n.link}`).join('\n\n');
    addLog(`├─ [변수] text.length = ${text.length} 문자`, 'data');
    
    try {
        // Electron clipboard API 사용 (우선순위)
        if (window.electronAPI && window.electronAPI.clipboard) {
            window.electronAPI.clipboard.writeText(text);
        } else {
            // 브라우저 환경 fallback
            await navigator.clipboard.writeText(text);
        }
        addLog('├─ [성공] 클립보드에 복사됨', 'success');
        addLog('[함수종료] copySelectedNews() - 성공', 'debug');
        addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
        addLog(`✅ ${selectedNews.length}개 기사 복사 완료`, 'success');
    } catch (error) {
        addLog(`├─ [에러] ${error.message}`, 'error');
        addLog('[함수종료] copySelectedNews() - 실패', 'debug');
        addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
        addLog(`❌ 복사 실패: ${error.message}`, 'error');
    }
}

// ========== Clipping Page Functions ==========
const crawlerPageContainer = document.querySelector('.container');
const clippingPage = document.getElementById('clipping-page');
const backToCrawlerBtn = document.getElementById('back-to-crawler-btn');
let crawlerPageElements = null;

const clippingListContainer = document.getElementById('clipping-list-container');
const clippingDetailModal = document.getElementById('clipping-detail-modal');
const clippingDetailModalOverlay = document.getElementById('clipping-detail-modal-overlay');
const closeClippingDetailBtn = document.getElementById('close-clipping-detail-btn');
let keywords = [];
let currentClippingId = null;

/**
 * 크롤러 페이지 요소 초기화
 */
function initializeCrawlerPage() {
    addLog('[함수호출] initializeCrawlerPage()', 'debug');
    
    if (!crawlerPageElements) {
        crawlerPageElements = {
            topSection: crawlerPageContainer?.querySelector('.top-section'),
            toolbarSection: crawlerPageContainer?.querySelector('.toolbar'),
            mainContent: crawlerPageContainer?.querySelector('.main-content-split')
        };
        addLog('├─ [변수할당] crawlerPageElements 초기화 완료', 'data');
    }
    
    addLog('[함수종료] initializeCrawlerPage()', 'debug');
}

/**
 * 클리핑 페이지 표시
 */
function showClippingPage() {
    addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
    addLog('[함수호출] showClippingPage()', 'debug');
    
    initializeCrawlerPage();
    
    // 크롤러 페이지 요소 숨김
    if (crawlerPageElements) {
        if (crawlerPageElements.topSection) {
            crawlerPageElements.topSection.style.display = 'none';
            addLog('├─ [DOM조작] topSection.style.display = "none"', 'dom');
        }
        if (crawlerPageElements.toolbarSection) {
            crawlerPageElements.toolbarSection.style.display = 'none';
            addLog('├─ [DOM조작] toolbarSection.style.display = "none"', 'dom');
        }
        if (crawlerPageElements.mainContent) {
            crawlerPageElements.mainContent.style.display = 'none';
            addLog('├─ [DOM조작] mainContent.style.display = "none"', 'dom');
        }
    }
    
    // 클리핑 페이지 표시
    if (clippingPage) {
        clippingPage.classList.add('active');
        addLog('├─ [DOM조작] clippingPage.classList.add("active")', 'dom');
    }
    
    addLog('├─ [함수호출] loadClippings()', 'debug');
    loadClippings();
    
    addLog('├─ [함수호출] attachClippingButtonEvents()', 'debug');
    attachClippingButtonEvents();
    
    addLog('[함수종료] showClippingPage() - 성공', 'debug');
    addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
    addLog('ℹ️ 클리핑 페이지로 이동', 'info');
}

/**
 * 크롤러 페이지로 복귀
 */
function showCrawlerPage() {
    addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
    addLog('[함수호출] showCrawlerPage()', 'debug');
    
    initializeCrawlerPage();
    
    // 크롤러 페이지 요소 표시
    if (crawlerPageElements) {
        if (crawlerPageElements.topSection) {
            crawlerPageElements.topSection.style.display = 'block';
            addLog('├─ [DOM조작] topSection.style.display = "block"', 'dom');
        }
        if (crawlerPageElements.toolbarSection) {
            crawlerPageElements.toolbarSection.style.display = 'block';
            addLog('├─ [DOM조작] toolbarSection.style.display = "block"', 'dom');
        }
        if (crawlerPageElements.mainContent) {
            crawlerPageElements.mainContent.style.display = 'flex';
            addLog('├─ [DOM조작] mainContent.style.display = "flex"', 'dom');
        }
    }
    
    // 클리핑 페이지 숨김
    if (clippingPage) {
        clippingPage.classList.remove('active');
        addLog('├─ [DOM조작] clippingPage.classList.remove("active")', 'dom');
    }
    
    addLog('[함수종료] showCrawlerPage() - 성공', 'debug');
    addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
    addLog('ℹ️ 크롤러 페이지로 복귀', 'info');
}

/**
 * 클리핑 목록 로드
 */
async function loadClippings() {
    addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
    addLog('[함수호출] loadClippings()', 'debug');
    
    const container = document.getElementById('clipping-list-container');
    
    // DOM 확인 (재시도 로직)
    if (!container) {
        addLog('├─ [DOM확인] clipping-list-container = null → 5ms 후 재시도', 'dom');
        setTimeout(loadClippings, 5);
        return;
    }
    addLog('├─ [DOM확인] clipping-list-container = <div>', 'dom');
    
    try {
        addLog('├─ [API호출] GET /api/clipping/list', 'api');
        const response = await fetch('/api/clipping/list');
        addLog(`│  ├─ [응답수신] ${response.status} ${response.statusText}`, 'api');
        
        const result = await response.json();
        addLog(`│  ├─ [응답파싱] JSON 파싱 완료`, 'api');
        addLog(`│  ├─ [응답데이터] success = ${result.success}`, 'api');
        addLog(`│  └─ [응답데이터] data.length = ${result.data?.length || 0}`, 'api');
        
        // 조건 분기: 데이터 존재 여부
        if (result.success && result.data.length > 0) {
            addLog('├─ [조건분기] data.length > 0 → 목록 렌더링', 'branch');
            addLog('├─ [함수호출] renderClippings(result.data)', 'debug');
            renderClippings(result.data);
        } else {
            addLog('├─ [조건분기] data.length = 0 → 빈 상태 렌더링', 'branch');
            addLog('├─ [함수호출] renderEmptyClipping()', 'debug');
            renderEmptyClipping();
        }
        
        addLog('[함수종료] loadClippings() - 성공', 'debug');
        addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
    } catch (error) {
        addLog(`├─ [예외발생] ${error.name}: ${error.message}`, 'error');
        addLog('├─ [함수호출] renderEmptyClipping()', 'debug');
        renderEmptyClipping();
        addLog('[함수종료] loadClippings() - 예외 발생', 'debug');
        addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
        addLog(`❌ 클리핑 로드 오류: ${error.message}`, 'error');
    }
}

/**
 * 클리핑 목록 렌더링
 * @param {Array} clippings - 클리핑 배열
 */
function renderClippings(clippings) {
    addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
    addLog('[함수호출] renderClippings()', 'debug');
    addLog(`├─ [파라미터] clippings.length = ${clippings?.length || 'null'}`, 'debug');
    
    const container = document.getElementById('clipping-list-container');
    if (!container) {
        addLog('├─ [에러] clipping-list-container = null', 'error');
        addLog('[함수종료] renderClippings() - 실패', 'debug');
        addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
        return;
    }
    
    addLog(`├─ [반복시작] map ${clippings.length}회`, 'loop');
    container.innerHTML = clippings.map(c => `
        <div class="clipping-item">
            <div class="clipping-item-info">
                <div class="clipping-item-name">${c.name}</div>
                <div class="clipping-item-meta">
                    <span class="clipping-keywords">${c.keywords ? c.keywords.join(', ') : ''}</span>
                    <span class="clipping-time">${c.send_time || ''}</span>
                </div>
            </div>
            <div class="clipping-item-actions">
                <label class="toggle-switch" title="${c.is_active ? '전송 ON' : '전송 OFF'}">
                    <input type="checkbox" data-clipping-id="${c.id}" class="toggle-clipping" ${c.is_active ? 'checked' : ''}>
                    <span class="toggle-slider"></span>
                </label>
                <button data-clipping-id="${c.id}" class="btn-open-clipping">열기</button>
                <button data-clipping-id="${c.id}" class="btn-delete-clipping">삭제</button>
            </div>
        </div>
    `).join('');
    addLog('├─ [반복종료] HTML 생성 완료', 'loop');
    addLog('├─ [DOM조작] container.innerHTML 설정 완료', 'dom');
    
    // 이벤트 바인딩
    setTimeout(() => {
        addLog('├─ [이벤트바인딩] 버튼 이벤트 등록 시작', 'debug');
        
        // 토글 스위치 이벤트
        container.querySelectorAll('.toggle-clipping').forEach(toggle => {
            const id = toggle.getAttribute('data-clipping-id');
            toggle.onchange = (e) => {
                e.stopPropagation();
                toggleClippingActive(id, toggle.checked);
            };
        });
        addLog(`│  ├─ [이벤트] 토글 스위치 ${clippings.length}개 등록`, 'debug');
        
        container.querySelectorAll('.btn-open-clipping').forEach(btn => {
            const id = btn.getAttribute('data-clipping-id');
            btn.onclick = () => editClipping(id);
        });
        addLog(`│  ├─ [이벤트] 열기 버튼 ${clippings.length}개 등록`, 'debug');
        
        container.querySelectorAll('.btn-delete-clipping').forEach(btn => {
            const id = btn.getAttribute('data-clipping-id');
            btn.onclick = () => deleteClipping(id);
        });
        addLog(`│  └─ [이벤트] 삭제 버튼 ${clippings.length}개 등록`, 'debug');
    }, 0);
    
    addLog('[함수종료] renderClippings() - 성공', 'debug');
    addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
}

/**
 * 빈 클리핑 상태 렌더링
 */
function renderEmptyClipping() {
    addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
    addLog('[함수호출] renderEmptyClipping()', 'debug');
    
    const container = document.getElementById('clipping-list-container');
    if (!container) {
        addLog('├─ [에러] clipping-list-container = null', 'error');
        addLog('[함수종료] renderEmptyClipping() - 실패', 'debug');
        addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
        return;
    }
    
    container.innerHTML = `
        <div class="clipping-empty">
            <div class="empty-icon">📝</div>
            <h3>생성된 클리핑이 없습니다</h3>
            <button id="btn-create-empty-dynamic" class="btn-create-empty">➕ 새로 생성</button>
        </div>
    `;
    addLog('├─ [DOM조작] 빈 상태 HTML 설정 완료', 'dom');
    
    // 동적 버튼 이벤트 바인딩
    setTimeout(() => {
        const btn = document.getElementById('btn-create-empty-dynamic');
        if (btn) {
            btn.onclick = () => showClippingDetail();
            addLog('├─ [이벤트] btn-create-empty-dynamic.onclick 등록', 'debug');
        }
    }, 0);
    
    addLog('[함수종료] renderEmptyClipping() - 성공', 'debug');
    addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
}

/**
 * 클리핑 상세 모달 표시
 * @param {number|null} clippingId - 클리핑 ID (null이면 새로 생성)
 */
function showClippingDetail(clippingId = null) {
    addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
    addLog('[함수호출] showClippingDetail()', 'debug');
    addLog(`├─ [파라미터] clippingId = ${clippingId}`, 'debug');
    
    currentClippingId = clippingId || null;
    keywords = [];
    addLog('├─ [변수할당] currentClippingId, keywords 초기화', 'data');
    
    // 폼 초기화
    if (document.getElementById('clipping-name')) document.getElementById('clipping-name').value = '';
    if (document.getElementById('repeat-type')) document.getElementById('repeat-type').value = 'daily';
    if (document.getElementById('send-time')) document.getElementById('send-time').value = '09:00';
    if (document.getElementById('max-articles')) document.getElementById('max-articles').value = '10';
    if (document.getElementById('include-summary')) document.getElementById('include-summary').checked = true;
    if (document.getElementById('include-links')) document.getElementById('include-links').checked = true;
    if (document.getElementById('slack-webhook-url')) document.getElementById('slack-webhook-url').value = '';
    addLog('├─ [DOM조작] 폼 필드 초기화 완료', 'dom');
    
    renderKeywords();
    
    // 모달 표시
    if (clippingDetailModalOverlay) {
        clippingDetailModalOverlay.classList.add('visible');
        addLog('├─ [DOM조작] modalOverlay.classList.add("visible")', 'dom');
    }
    if (clippingDetailModal) {
        clippingDetailModal.classList.add('visible');
        addLog('├─ [DOM조작] modal.classList.add("visible")', 'dom');
    }
    
    addLog('[함수종료] showClippingDetail() - 성공', 'debug');
    addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
    addLog('ℹ️ 클리핑 상세 모달 열림', 'info');
}

/**
 * 클리핑 상세 모달 닫기
 */
function closeClippingDetail() {
    addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
    addLog('[함수호출] closeClippingDetail()', 'debug');
    
    if (clippingDetailModalOverlay) {
        clippingDetailModalOverlay.classList.remove('visible');
        addLog('├─ [DOM조작] modalOverlay.classList.remove("visible")', 'dom');
    }
    if (clippingDetailModal) {
        clippingDetailModal.classList.remove('visible');
        addLog('├─ [DOM조작] modal.classList.remove("visible")', 'dom');
    }
    
    currentClippingId = null;
    keywords = [];
    addLog('├─ [변수할당] currentClippingId, keywords 초기화', 'data');
    
    addLog('[함수종료] closeClippingDetail() - 성공', 'debug');
    addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
    addLog('ℹ️ 클리핑 상세 모달 닫힘', 'info');
}

/**
 * 키워드 추가
 * @param {string} keyword - 추가할 키워드
 */
function addKeyword(keyword) {
    addLog('[함수호출] addKeyword()', 'debug');
    addLog(`├─ [파라미터] keyword = "${keyword}"`, 'debug');
    
    if (!keyword.trim()) {
        addLog('├─ [조건분기] keyword 빈 문자열 → 종료', 'branch');
        addLog('[함수종료] addKeyword() - 빈 문자열', 'debug');
        return;
    }
    
    if (keywords.includes(keyword)) {
        addLog('├─ [조건분기] keyword 중복 → 종료', 'branch');
        addLog('[함수종료] addKeyword() - 중복', 'debug');
        return;
    }
    
    keywords.push(keyword);
    addLog(`├─ [배열조작] keywords.push("${keyword}")`, 'data');
    addLog(`├─ [변수] keywords.length = ${keywords.length}`, 'data');
    
    renderKeywords();
    addLog('[함수종료] addKeyword() - 성공', 'debug');
}

/**
 * 키워드 제거
 * @param {string} keyword - 제거할 키워드
 */
function removeKeyword(keyword) {
    addLog('[함수호출] removeKeyword()', 'debug');
    addLog(`├─ [파라미터] keyword = "${keyword}"`, 'debug');
    
    const beforeLength = keywords.length;
    keywords = keywords.filter(k => k !== keyword);
    const afterLength = keywords.length;
    
    addLog(`├─ [배열조작] keywords.filter()`, 'data');
    addLog(`├─ [변수] 이전 길이 = ${beforeLength}, 이후 길이 = ${afterLength}`, 'data');
    
    renderKeywords();
    addLog('[함수종료] removeKeyword() - 성공', 'debug');
}

/**
 * 키워드 렌더링
 */
function renderKeywords() {
    addLog('[함수호출] renderKeywords()', 'debug');
    addLog(`├─ [변수] keywords.length = ${keywords.length}`, 'data');
    
    const input = document.getElementById('keyword-input');
    const container = document.getElementById('keywords-input');
    
    if (!container) {
        addLog('├─ [에러] keywords-input = null', 'error');
        addLog('[함수종료] renderKeywords() - 실패', 'debug');
        return;
    }
    
    // 기존 태그 제거
    container.querySelectorAll('.keyword-tag').forEach(tag => tag.remove());
    addLog('├─ [DOM조작] 기존 태그 제거 완료', 'dom');
    
    // 키워드 태그 생성
    keywords.forEach(kw => {
        const tag = document.createElement('div');
        tag.className = 'keyword-tag';
        tag.innerHTML = `${kw}<button onclick="removeKeyword('${kw}')">X</button>`;
        if (input) {
            container.insertBefore(tag, input);
        } else {
            container.appendChild(tag);
        }
    });
    addLog(`├─ [DOM조작] ${keywords.length}개 태그 생성 완료`, 'dom');
    
    // 입력 필드 재배치
    if (input && !input.parentNode) {
        container.appendChild(input);
        addLog('├─ [DOM조작] input 재배치', 'dom');
    }
    
    // 이벤트 재등록
    if (input) {
        input.onkeypress = (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                addKeyword(input.value);
                input.value = '';
            }
        };
        addLog('├─ [이벤트] input.onkeypress 재등록', 'debug');
    }
    
    addLog('[함수종료] renderKeywords() - 성공', 'debug');
}

/**
 * 클리핑 저장
 */
async function saveClipping() {
    addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
    addLog('[함수호출] saveClipping()', 'debug');
    
    const name = document.getElementById('clipping-name')?.value || '';
    addLog(`├─ [변수] name = "${name}"`, 'data');
    addLog(`├─ [변수] keywords.length = ${keywords.length}`, 'data');
    
    // 조건 분기: 유효성 검사
    if (!name.trim() || keywords.length === 0) {
        addLog('├─ [조건분기] name 또는 keywords 없음 → 경고', 'branch');
        addLog('[함수종료] saveClipping() - 유효성 검사 실패', 'debug');
        addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
        alert('이름과 키워드를 입력해주세요');
        addLog('⚠️ 이름과 키워드를 입력해주세요', 'warning');
        return;
    }
    
    addLog('├─ [조건분기] 유효성 검사 통과 → 저장 진행', 'branch');
    
    const data = {
        name,
        keywords,
        repeat_type: document.getElementById('repeat-type')?.value || 'daily',
        repeat_days: [],
        send_time: document.getElementById('send-time')?.value || '09:00',
        max_articles: parseInt(document.getElementById('max-articles')?.value || '10'),
        include_summary: document.getElementById('include-summary')?.checked || true,
        include_links: document.getElementById('include-links')?.checked || true,
        slack_webhook_url: document.getElementById('slack-webhook-url')?.value || ''
    };
    addLog(`├─ [변수] data = ${JSON.stringify(data).substring(0, 100)}...`, 'data');
    
    try {
        const url = currentClippingId ? `/api/clipping/${currentClippingId}` : '/api/clipping/create';
        const method = currentClippingId ? 'PUT' : 'POST';
        
        addLog(`├─ [API호출] ${method} ${url}`, 'api');
        addLog(`│  ├─ [요청메소드] ${method}`, 'api');
        addLog(`│  ├─ [요청바디] ${JSON.stringify(data).substring(0, 100)}...`, 'api');
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        addLog(`│  ├─ [응답수신] ${response.status} ${response.statusText}`, 'api');
        
        const result = await response.json();
        addLog(`│  └─ [응답데이터] success = ${result.success}`, 'api');
        
        // 조건 분기: 저장 성공 여부
        if (result.success) {
            addLog('├─ [조건분기] result.success = true → 저장 성공', 'branch');
            alert('저장되었습니다');
            closeClippingDetail();
            loadClippings();
            addLog('[함수종료] saveClipping() - 성공', 'debug');
            addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
            addLog('✅ 클리핑 저장 완료', 'success');
        } else {
            addLog('├─ [조건분기] result.success = false → 저장 실패', 'branch');
            alert('저장에 실패했습니다');
            addLog('[함수종료] saveClipping() - 실패', 'debug');
            addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
            addLog('❌ 클리핑 저장 실패', 'error');
        }
    } catch (error) {
        addLog(`├─ [예외발생] ${error.name}: ${error.message}`, 'error');
        alert('오류가 발생했습니다');
        addLog('[함수종료] saveClipping() - 예외 발생', 'debug');
        addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
        addLog(`❌ 클리핑 저장 오류: ${error.message}`, 'error');
    }
}

/**
 * 클리핑 삭제
 * @param {number} clippingId - 클리핑 ID
 */
/**
 * 클리핑 활성화/비활성화 토글
 * @param {number} clippingId - 클리핑 ID
 * @param {boolean} isActive - 활성화 상태
 */
async function toggleClippingActive(clippingId, isActive) {
    addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
    addLog('[함수호출] toggleClippingActive()', 'debug');
    addLog(`├─ [파라미터] clippingId = ${clippingId}`, 'debug');
    addLog(`├─ [파라미터] isActive = ${isActive}`, 'debug');
    
    try {
        addLog(`├─ [API호출] PATCH /api/clipping/${clippingId}/toggle 시작`, 'api');
        const response = await fetch(`/api/clipping/${clippingId}/toggle`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_active: isActive })
        });
        addLog('├─ [API응답] 수신 완료', 'api');
        addLog(`│  ├─ status = ${response.status}`, 'api');
        
        const result = await response.json();
        addLog(`│  └─ result.success = ${result.success}`, 'api');
        
        if (result.success) {
            addLog(`✅ 클리핑 ${isActive ? '활성화' : '비활성화'} 완료`, 'success');
            addLog('[함수종료] toggleClippingActive() - 성공', 'debug');
        } else {
            addLog(`├─ [에러] ${result.error}`, 'error');
            addLog('[함수종료] toggleClippingActive() - 실패', 'debug');
            alert(`오류: ${result.error}`);
            // 실패 시 토글 상태 되돌리기
            const toggle = document.querySelector(`.toggle-clipping[data-clipping-id="${clippingId}"]`);
            if (toggle) toggle.checked = !isActive;
        }
        addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
    } catch (error) {
        addLog(`├─ [예외발생] ${error.name}: ${error.message}`, 'error');
        addLog('[함수종료] toggleClippingActive() - 예외 발생', 'debug');
        addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
        alert(`오류: ${error.message}`);
        // 실패 시 토글 상태 되돌리기
        const toggle = document.querySelector(`.toggle-clipping[data-clipping-id="${clippingId}"]`);
        if (toggle) toggle.checked = !isActive;
    }
}

async function deleteClipping(clippingId) {
    addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
    addLog('[함수호출] deleteClipping()', 'debug');
    addLog(`├─ [파라미터] clippingId = ${clippingId}`, 'debug');
    
    if (!confirm('정말 삭제하시겠습니까?')) {
        addLog('├─ [조건분기] 사용자 취소 → 종료', 'branch');
        addLog('[함수종료] deleteClipping() - 취소', 'debug');
        addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
        return;
    }
    
    addLog('├─ [조건분기] 사용자 확인 → 삭제 진행', 'branch');
    
    try {
        addLog(`├─ [API호출] DELETE /api/clipping/${clippingId}`, 'api');
        const response = await fetch(`/api/clipping/${clippingId}`, { method: 'DELETE' });
        addLog(`│  ├─ [응답수신] ${response.status} ${response.statusText}`, 'api');
        
        const result = await response.json();
        addLog(`│  └─ [응답데이터] success = ${result.success}`, 'api');
        
        if (result.success) {
            addLog('├─ [조건분기] result.success = true → 삭제 성공', 'branch');
            loadClippings();
            addLog('[함수종료] deleteClipping() - 성공', 'debug');
            addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
            addLog('✅ 클리핑 삭제 완료', 'success');
        }
    } catch (error) {
        addLog(`├─ [예외발생] ${error.name}: ${error.message}`, 'error');
        addLog('[함수종료] deleteClipping() - 예외 발생', 'debug');
        addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
        addLog(`❌ 클리핑 삭제 오류: ${error.message}`, 'error');
    }
}

/**
 * 클리핑 편집
 * @param {number} clippingId - 클리핑 ID
 */
function editClipping(clippingId) {
    addLog('[함수호출] editClipping()', 'debug');
    addLog(`├─ [파라미터] clippingId = ${clippingId}`, 'debug');
    showClippingDetail(clippingId);
    addLog('[함수종료] editClipping()', 'debug');
}

/**
 * 클리핑 버튼 이벤트 연결
 */
function attachClippingButtonEvents() {
    addLog('[함수호출] attachClippingButtonEvents()', 'debug');
    
    if (document.getElementById('create-clipping-btn')) {
        document.getElementById('create-clipping-btn').onclick = () => showClippingDetail();
        addLog('├─ [이벤트] create-clipping-btn.onclick 등록', 'debug');
    }
    if (document.getElementById('create-clipping-empty-btn')) {
        document.getElementById('create-clipping-empty-btn').onclick = () => showClippingDetail();
        addLog('├─ [이벤트] create-clipping-empty-btn.onclick 등록', 'debug');
    }
    if (document.getElementById('cancel-clipping-btn')) {
        document.getElementById('cancel-clipping-btn').onclick = closeClippingDetail;
        addLog('├─ [이벤트] cancel-clipping-btn.onclick 등록', 'debug');
    }
    if (document.getElementById('save-clipping-btn')) {
        document.getElementById('save-clipping-btn').onclick = saveClipping;
        addLog('├─ [이벤트] save-clipping-btn.onclick 등록', 'debug');
    }
    
    addLog('[함수종료] attachClippingButtonEvents()', 'debug');
}

// ========== 저장 목록 기능 ==========
/**
 * 선택한 기사 저장 (자동 이름 생성)
 */
async function saveSelectedArticles() {
    addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
    addLog('[함수호출] saveSelectedArticles()', 'debug');
    addLog(`├─ [변수] selectedNews.length = ${selectedNews.length}`, 'data');
    
    if (selectedNews.length === 0) {
        addLog('├─ [조건분기] selectedNews.length = 0 → 경고 후 종료', 'branch');
        addLog('[함수종료] saveSelectedArticles() - 선택 없음', 'debug');
        addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
        alert('선택된 기사가 없습니다');
        return;
    }
    
    // 자동으로 이름 생성: "키워드_날짜" 형식
    const keyword = document.getElementById('keyword-input-toolbar')?.value || '뉴스';
    const dateStr = new Date().toISOString().split('T')[0].replace(/-/g, '');
    const listName = `${keyword}_${dateStr}`;
    
    addLog(`├─ [자동생성] 목록 이름 = "${listName}"`, 'data');
    
    try {
        addLog(`├─ [API호출] POST /api/saved-lists`, 'api');
        addLog(`│  ├─ name = "${listName}"`, 'api');
        addLog(`│  └─ articles.length = ${selectedNews.length}`, 'api');
        
        const response = await fetch('/api/saved-lists', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: listName,
                articles: selectedNews
            })
        });
        
        addLog(`├─ [API응답] status = ${response.status}`, 'api');
        const result = await response.json();
        addLog(`├─ [API응답] success = ${result.success}`, 'api');
        
        if (result.success) {
            addLog(`✅ ${selectedNews.length}개 기사 저장 완료`, 'success');
            addLog('[함수종료] saveSelectedArticles() - 성공', 'debug');
            addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
            
            // 저장 후 저장목록 패널 자동 열기
            showSavedListPanel();
        } else {
            addLog(`├─ [에러] ${result.error}`, 'error');
            addLog('[함수종료] saveSelectedArticles() - 실패', 'debug');
            addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
            alert(`저장 실패: ${result.error}`);
        }
    } catch (error) {
        addLog(`├─ [예외발생] ${error.name}: ${error.message}`, 'error');
        addLog('[함수종료] saveSelectedArticles() - 예외', 'debug');
        addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
        alert(`저장 중 오류 발생: ${error.message}`);
    }
}

/**
 * 저장목록 패널 표시
 */
async function showSavedListPanel() {
    addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
    addLog('[함수호출] showSavedListPanel()', 'debug');
    
    const panel = document.getElementById('saved-list-panel');
    const overlay = document.getElementById('saved-list-modal-overlay');
    const container = document.getElementById('saved-list-container');
    const emptyState = document.getElementById('saved-list-empty');
    
    if (!panel || !overlay || !container) {
        addLog('├─ [에러] 필수 DOM 요소를 찾을 수 없음', 'error');
        addLog('[함수종료] showSavedListPanel() - DOM 없음', 'debug');
        addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
        return;
    }
    
    try {
        addLog('├─ [API호출] GET /api/saved-lists', 'api');
        const response = await fetch('/api/saved-lists');
        addLog(`├─ [API응답] status = ${response.status}`, 'api');
        
        const result = await response.json();
        addLog(`├─ [API응답] success = ${result.success}, lists.length = ${result.lists?.length || 0}`, 'api');
        
        if (result.success) {
            if (result.lists.length === 0) {
                addLog('├─ [조건분기] 저장된 목록 없음 → 빈 상태 표시', 'branch');
                container.innerHTML = '';
                if (emptyState) emptyState.style.display = 'block';
            } else {
                addLog('├─ [조건분기] 저장된 목록 있음 → 렌더링', 'branch');
                if (emptyState) emptyState.style.display = 'none';
                renderSavedLists(result.lists);
            }
            
            addLog('├─ [DOM조작] 패널 및 오버레이 표시', 'dom');
            panel.style.display = 'block';
            overlay.style.display = 'block';
            
            addLog('[함수종료] showSavedListPanel() - 성공', 'debug');
            addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
        } else {
            addLog(`├─ [에러] ${result.error}`, 'error');
            addLog('[함수종료] showSavedListPanel() - 실패', 'debug');
            addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
            alert(`목록 불러오기 실패: ${result.error}`);
        }
    } catch (error) {
        addLog(`├─ [예외발생] ${error.name}: ${error.message}`, 'error');
        addLog('[함수종료] showSavedListPanel() - 예외', 'debug');
        addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
        alert(`목록 불러오기 중 오류 발생: ${error.message}`);
    }
}

/**
 * 저장 목록 렌더링
 */
function renderSavedLists(lists) {
    addLog('[함수호출] renderSavedLists()', 'debug');
    addLog(`├─ [파라미터] lists.length = ${lists.length}`, 'debug');
    
    const container = document.getElementById('saved-list-container');
    if (!container) {
        addLog('├─ [에러] saved-list-container 없음', 'error');
        return;
    }
    
    container.innerHTML = lists.map(list => `
        <div class="saved-list-item" data-list-id="${list.id}">
            <div class="saved-list-item-info">
                <div class="saved-list-item-name">${list.name}</div>
                <div class="saved-list-item-meta">
                    <span>${list.article_count}개 기사</span>
                    <span>${new Date(list.created_at).toLocaleString('ko-KR')}</span>
                </div>
            </div>
            <div class="saved-list-item-actions">
                <button class="btn-view-list" data-list-id="${list.id}">보기</button>
                <button class="btn-delete-list" data-list-id="${list.id}">삭제</button>
            </div>
        </div>
    `).join('');
    
    addLog('├─ [DOM조작] 목록 HTML 렌더링 완료', 'dom');
    
    // 이벤트 바인딩
    setTimeout(() => {
        container.querySelectorAll('.btn-view-list').forEach(btn => {
            const listId = btn.getAttribute('data-list-id');
            btn.onclick = () => viewSavedList(listId);
        });
        
        container.querySelectorAll('.btn-delete-list').forEach(btn => {
            const listId = btn.getAttribute('data-list-id');
            btn.onclick = () => deleteSavedList(listId);
        });
        
        addLog(`├─ [이벤트] ${lists.length}개 목록 버튼 이벤트 바인딩 완료`, 'debug');
        addLog('[함수종료] renderSavedLists()', 'debug');
    }, 0);
}

/**
 * 저장 목록 상세 보기
 */
async function viewSavedList(listId) {
    addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
    addLog('[함수호출] viewSavedList()', 'debug');
    addLog(`├─ [파라미터] listId = ${listId}`, 'debug');
    
    try {
        addLog(`├─ [API호출] GET /api/saved-lists/${listId}`, 'api');
        const response = await fetch(`/api/saved-lists/${listId}`);
        addLog(`├─ [API응답] status = ${response.status}`, 'api');
        
        const result = await response.json();
        
        if (result.success) {
            const list = result.list;
            addLog(`├─ [API응답] 목록명 = "${list.name}", 기사수 = ${list.articles.length}`, 'api');
            
            // 새 창에서 목록 표시 (또는 모달로 표시)
            let content = `${list.name}\n생성일: ${new Date(list.created_at).toLocaleString('ko-KR')}\n총 ${list.articles.length}개 기사\n\n`;
            content += list.articles.map((article, idx) => 
                `${idx + 1}. [${article.source}] ${article.title}\n   ${article.link}\n   ${article.published_time}\n`
            ).join('\n');
            
            // 텍스트 파일로 다운로드
            const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${list.name}.txt`;
            a.click();
            URL.revokeObjectURL(url);
            
            addLog('✅ 목록 다운로드 완료', 'success');
            addLog('[함수종료] viewSavedList() - 성공', 'debug');
            addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
        } else {
            addLog(`├─ [에러] ${result.error}`, 'error');
            addLog('[함수종료] viewSavedList() - 실패', 'debug');
            addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
            alert(`목록 불러오기 실패: ${result.error}`);
        }
    } catch (error) {
        addLog(`├─ [예외발생] ${error.name}: ${error.message}`, 'error');
        addLog('[함수종료] viewSavedList() - 예외', 'debug');
        addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
        alert(`목록 불러오기 중 오류 발생: ${error.message}`);
    }
}

/**
 * 저장 목록 삭제
 */
async function deleteSavedList(listId) {
    addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
    addLog('[함수호출] deleteSavedList()', 'debug');
    addLog(`├─ [파라미터] listId = ${listId}`, 'debug');
    
    if (!confirm('이 목록을 삭제하시겠습니까?')) {
        addLog('├─ [조건분기] 사용자가 취소함', 'branch');
        addLog('[함수종료] deleteSavedList() - 취소', 'debug');
        addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
        return;
    }
    
    try {
        addLog(`├─ [API호출] DELETE /api/saved-lists/${listId}`, 'api');
        const response = await fetch(`/api/saved-lists/${listId}`, {
            method: 'DELETE'
        });
        addLog(`├─ [API응답] status = ${response.status}`, 'api');
        
        const result = await response.json();
        
        if (result.success) {
            addLog('✅ 목록 삭제 완료', 'success');
            addLog('[함수종료] deleteSavedList() - 성공', 'debug');
            addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
            
            // 목록 새로고침
            showSavedListPanel();
        } else {
            addLog(`├─ [에러] ${result.error}`, 'error');
            addLog('[함수종료] deleteSavedList() - 실패', 'debug');
            addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
            alert(`삭제 실패: ${result.error}`);
        }
    } catch (error) {
        addLog(`├─ [예외발생] ${error.name}: ${error.message}`, 'error');
        addLog('[함수종료] deleteSavedList() - 예외', 'debug');
        addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
        alert(`삭제 중 오류 발생: ${error.message}`);
    }
}

/**
 * 저장목록 패널 닫기
 */
function closeSavedListPanel() {
    addLog('[함수호출] closeSavedListPanel()', 'debug');
    
    const panel = document.getElementById('saved-list-panel');
    const overlay = document.getElementById('saved-list-modal-overlay');
    
    if (panel) panel.style.display = 'none';
    if (overlay) overlay.style.display = 'none';
    
    addLog('├─ [DOM조작] 패널 및 오버레이 숨김', 'dom');
    addLog('[함수종료] closeSavedListPanel()', 'debug');
}

/**
 * 모든 저장 목록 삭제
 */
async function deleteAllSavedLists() {
    addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
    addLog('[함수호출] deleteAllSavedLists()', 'debug');
    
    if (!confirm('모든 저장 목록을 삭제하시겠습니까?')) {
        addLog('├─ [조건분기] 사용자가 취소함', 'branch');
        addLog('[함수종료] deleteAllSavedLists() - 취소', 'debug');
        addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
        return;
    }
    
    try {
        addLog('├─ [API호출] DELETE /api/saved-lists/all', 'api');
        const response = await fetch('/api/saved-lists/all', {
            method: 'DELETE'
        });
        addLog(`├─ [API응답] status = ${response.status}`, 'api');
        
        const result = await response.json();
        
        if (result.success) {
            addLog('✅ 전체 목록 삭제 완료', 'success');
            addLog('[함수종료] deleteAllSavedLists() - 성공', 'debug');
            addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
            
            // 목록 새로고침
            showSavedListPanel();
        } else {
            addLog(`├─ [에러] ${result.error}`, 'error');
            addLog('[함수종료] deleteAllSavedLists() - 실패', 'debug');
            addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
            alert(`삭제 실패: ${result.error}`);
        }
    } catch (error) {
        addLog(`├─ [예외발생] ${error.name}: ${error.message}`, 'error');
        addLog('[함수종료] deleteAllSavedLists() - 예외', 'debug');
        addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
        alert(`삭제 중 오류 발생: ${error.message}`);
    }
}

// ========== 필터 및 정렬 기능 ==========
/**
 * 기사 필터링 및 정렬 적용
 */
function applyFiltersAndSort() {
    addLog('[함수호출] applyFiltersAndSort()', 'debug');
    
    const filterInput = document.getElementById('article-filter-input');
    const dateFilter = document.getElementById('date-filter');
    const sortFilter = document.getElementById('sort-filter');
    
    const filterText = filterInput ? filterInput.value.toLowerCase() : '';
    const dateValue = dateFilter ? dateFilter.value : 'all';
    const sortValue = sortFilter ? sortFilter.value : 'desc';
    
    addLog(`├─ [변수] filterText = "${filterText}"`, 'data');
    addLog(`├─ [변수] dateValue = "${dateValue}"`, 'data');
    addLog(`├─ [변수] sortValue = "${sortValue}"`, 'data');
    
    // 구글 뉴스 필터링 및 정렬
    let filteredGoogle = [...allNewsData];
    
    // 텍스트 필터
    if (filterText) {
        filteredGoogle = filteredGoogle.filter(news => 
            news.title.toLowerCase().includes(filterText) ||
            news.source.toLowerCase().includes(filterText)
        );
        addLog(`├─ [필터] 텍스트 필터 적용 후: ${filteredGoogle.length}개`, 'debug');
    }
    
    // 날짜 필터
    if (dateValue !== 'all') {
        const now = new Date();
        filteredGoogle = filteredGoogle.filter(news => {
            const newsDate = new Date(news.created_at);
            const diffDays = Math.floor((now - newsDate) / (1000 * 60 * 60 * 24));
            
            if (dateValue === 'today') return diffDays === 0;
            if (dateValue === 'week') return diffDays <= 7;
            if (dateValue === 'month') return diffDays <= 30;
            return true;
        });
        addLog(`├─ [필터] 날짜 필터 적용 후: ${filteredGoogle.length}개`, 'debug');
    }
    
    // 정렬
    filteredGoogle.sort((a, b) => {
        const dateA = new Date(a.created_at);
        const dateB = new Date(b.created_at);
        return sortValue === 'desc' ? dateB - dateA : dateA - dateB;
    });
    addLog(`├─ [정렬] ${sortValue === 'desc' ? '최신순' : '오래된순'} 정렬 완료`, 'debug');
    
    // 네이버 뉴스 필터링 및 정렬
    let filteredNaver = [...allNaverNewsData];
    
    if (filterText) {
        filteredNaver = filteredNaver.filter(news => 
            news.title.toLowerCase().includes(filterText) ||
            news.source.toLowerCase().includes(filterText)
        );
    }
    
    if (dateValue !== 'all') {
        const now = new Date();
        filteredNaver = filteredNaver.filter(news => {
            const newsDate = new Date(news.created_at);
            const diffDays = Math.floor((now - newsDate) / (1000 * 60 * 60 * 24));
            
            if (dateValue === 'today') return diffDays === 0;
            if (dateValue === 'week') return diffDays <= 7;
            if (dateValue === 'month') return diffDays <= 30;
            return true;
        });
    }
    
    filteredNaver.sort((a, b) => {
        const dateA = new Date(a.created_at);
        const dateB = new Date(b.created_at);
        return sortValue === 'desc' ? dateB - dateA : dateA - dateB;
    });
    
    // 렌더링
    renderNewsTable(filteredGoogle);
    renderNaverNewsTable(filteredNaver);
    
    addLog('[함수종료] applyFiltersAndSort()', 'debug');
    addLog(`✅ 필터 적용 완료: 구글 ${filteredGoogle.length}개, 네이버 ${filteredNaver.length}개`, 'success');
}

// ========== Event Listeners ==========
addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');
addLog('[시스템] 이벤트 리스너 등록 시작', 'system');

// 크롤링 버튼
if (crawlBtnToolbar) {
    crawlBtnToolbar.addEventListener('click', crawlNews);
    addLog('├─ [이벤트] crawlBtnToolbar.addEventListener("click", crawlNews)', 'debug');
}

// 키워드 입력 (Enter)
if (keywordInputToolbar) {
    keywordInputToolbar.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            crawlNews();
        }
    });
    addLog('├─ [이벤트] keywordInputToolbar.addEventListener("keypress")', 'debug');
}

// 선택 기사 복사
if (copySelectionBtn) {
    copySelectionBtn.addEventListener('click', copySelectedNews);
    addLog('├─ [이벤트] copySelectionBtn.addEventListener("click", copySelectedNews)', 'debug');
}

// 선택 기사 저장
const saveArticlesBtn = document.getElementById('save-articles-btn');
if (saveArticlesBtn) {
    saveArticlesBtn.addEventListener('click', saveSelectedArticles);
    addLog('├─ [이벤트] saveArticlesBtn.addEventListener("click", saveSelectedArticles)', 'debug');
}

// 저장목록 보기
const savedListBtn = document.getElementById('saved-list-btn');
if (savedListBtn) {
    savedListBtn.addEventListener('click', showSavedListPanel);
    addLog('├─ [이벤트] savedListBtn.addEventListener("click", showSavedListPanel)', 'debug');
}

// 저장목록 패널 닫기
const closeSavedListBtn = document.getElementById('close-saved-list-panel-btn');
if (closeSavedListBtn) {
    closeSavedListBtn.addEventListener('click', closeSavedListPanel);
    addLog('├─ [이벤트] closeSavedListBtn.addEventListener("click", closeSavedListPanel)', 'debug');
}

// 저장목록 오버레이 클릭
const savedListOverlay = document.getElementById('saved-list-modal-overlay');
if (savedListOverlay) {
    savedListOverlay.addEventListener('click', closeSavedListPanel);
    addLog('├─ [이벤트] savedListOverlay.addEventListener("click", closeSavedListPanel)', 'debug');
}

// 전체 삭제 버튼
const deleteAllSavedBtn = document.getElementById('delete-all-saved-btn');
if (deleteAllSavedBtn) {
    deleteAllSavedBtn.addEventListener('click', deleteAllSavedLists);
    addLog('├─ [이벤트] deleteAllSavedBtn.addEventListener("click", deleteAllSavedLists)', 'debug');
}

// 전체 선택 해제
if (clearAllSelectionBtn) {
    clearAllSelectionBtn.addEventListener('click', clearAllSelection);
    addLog('├─ [이벤트] clearAllSelectionBtn.addEventListener("click", clearAllSelection)', 'debug');
}

// 로그 토글
if (logToggleBtn) {
    logToggleBtn.addEventListener('click', () => {
        if (logFloatingPanel) {
            const isVisible = logFloatingPanel.style.display !== 'none';
            isLogPanelOpen = !isVisible;
            logFloatingPanel.style.display = isVisible ? 'none' : 'flex';
            
            // 패널이 열릴 때 로그 렌더링
            if (isLogPanelOpen) {
                renderLogs();
            }
            
            addLog(`ℹ️ 로그 패널 ${isVisible ? '닫힘' : '열림'}`, 'info');
        }
    });
    addLog('├─ [이벤트] logToggleBtn.addEventListener("click")', 'debug');
}

// 로그 닫기
if (closeLogBtn) {
    closeLogBtn.addEventListener('click', () => {
        if (logFloatingPanel) {
            isLogPanelOpen = false;
            logFloatingPanel.style.display = 'none';
            addLog('ℹ️ 로그 패널 닫힘', 'info');
        }
    });
    addLog('├─ [이벤트] closeLogBtn.addEventListener("click")', 'debug');
}

// 로그 지우기
if (clearLogBtnFloat) {
    clearLogBtnFloat.addEventListener('click', clearAllLogs);
    addLog('├─ [이벤트] clearLogBtnFloat.addEventListener("click", clearAllLogs)', 'debug');
}

// 최근 N줄 로그 복사 - HTML onclick으로 처리
// 전체 로그 복사 - HTML onclick으로 처리

// 기사 필터 입력
const articleFilterInput = document.getElementById('article-filter-input');
if (articleFilterInput) {
    articleFilterInput.addEventListener('input', applyFiltersAndSort);
    addLog('├─ [이벤트] articleFilterInput.addEventListener("input", applyFiltersAndSort)', 'debug');
}

// 날짜 필터
const dateFilterSelect = document.getElementById('date-filter');
if (dateFilterSelect) {
    dateFilterSelect.addEventListener('change', applyFiltersAndSort);
    addLog('├─ [이벤트] dateFilterSelect.addEventListener("change", applyFiltersAndSort)', 'debug');
}

// 정렬 필터
const sortFilterSelect = document.getElementById('sort-filter');
if (sortFilterSelect) {
    sortFilterSelect.addEventListener('change', applyFiltersAndSort);
    addLog('├─ [이벤트] sortFilterSelect.addEventListener("change", applyFiltersAndSort)', 'debug');
}

// 클리핑 페이지 버튼
const clippingPageBtn = document.getElementById('clipping-page-btn');
if (clippingPageBtn) {
    clippingPageBtn.onclick = showClippingPage;
    addLog('├─ [이벤트] clippingPageBtn.onclick = showClippingPage', 'debug');
}

// 크롤러 페이지 복귀 버튼
if (backToCrawlerBtn) {
    backToCrawlerBtn.addEventListener('click', showCrawlerPage);
    addLog('├─ [이벤트] backToCrawlerBtn.addEventListener("click", showCrawlerPage)', 'debug');
}

// 클리핑 모달 닫기
if (closeClippingDetailBtn) {
    closeClippingDetailBtn.addEventListener('click', closeClippingDetail);
    addLog('├─ [이벤트] closeClippingDetailBtn.addEventListener("click", closeClippingDetail)', 'debug');
}

// 클리핑 모달 오버레이 클릭
if (clippingDetailModalOverlay) {
    clippingDetailModalOverlay.addEventListener('click', (e) => {
        if (e.target === clippingDetailModalOverlay) {
            closeClippingDetail();
        }
    });
    addLog('├─ [이벤트] clippingDetailModalOverlay.addEventListener("click")', 'debug');
}

addLog('[시스템] 이벤트 리스너 등록 완료', 'system');
addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'system');

// 초기 로그 상태 업데이트
updateLogStatus();
addLog('✅ 시스템 초기화 완료. 뉴스 크롤링을 시작하세요.', 'success');

// 함수 등록 확인 로그
console.log('='.repeat(50));
console.log('[시스템] 전역 함수 등록 확인');
console.log('[시스템] window.copyRecentLogs:', typeof window.copyRecentLogs);
console.log('[시스템] window.copyRecentLogsFromInput:', typeof window.copyRecentLogsFromInput);
console.log('[시스템] window.copyAllLogs:', typeof window.copyAllLogs);
console.log('[시스템] window.clearAllLogs:', typeof window.clearAllLogs);
console.log('='.repeat(50));

// ========== 테스트 함수 ==========
/**
 * 간단한 테스트 복사 함수
 */
function testCopyFunction() {
    console.log('🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪');
    console.log('[테스트] testCopyFunction 호출됨!');
    console.log('[테스트] 이 메시지가 보이면 함수 호출 성공!');
    
    const testText = '테스트 복사 성공! 로그 텍스트입니다.';
    console.log('[테스트] 복사할 텍스트:', testText);
    
    try {
        // 방법 1: Electron clipboard
        if (window.electronAPI && window.electronAPI.clipboard) {
            console.log('[테스트] Electron clipboard API 사용');
            window.electronAPI.clipboard.writeText(testText);
            console.log('[테스트] Electron clipboard 복사 완료');
        } else {
            console.log('[테스트] 브라우저 clipboard API 사용');
            navigator.clipboard.writeText(testText).then(() => {
                console.log('[테스트] 브라우저 clipboard 복사 완료');
            }).catch(err => {
                console.error('[테스트] 브라우저 clipboard 복사 실패:', err);
            });
        }
        
        // 로그에도 표시
        if (logContainer) {
            const tempDiv = document.createElement('div');
            tempDiv.className = 'log-item success';
            tempDiv.style.background = '#ffebee';
            tempDiv.style.borderLeft = '3px solid #ff6b6b';
            tempDiv.textContent = `[${new Date().toLocaleTimeString('ko-KR')}] 🧪 테스트 복사 성공!`;
            logContainer.appendChild(tempDiv);
            logContainer.scrollTop = logContainer.scrollHeight;
        }
        
        alert('테스트 복사 성공! Ctrl+V로 붙여넣기 해보세요.');
        console.log('[테스트] 함수 실행 완료');
    } catch (error) {
        console.error('[테스트] 에러 발생:', error);
        alert('테스트 복사 실패: ' + error.message);
    }
    
    console.log('🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪');
}

// ========== 래퍼 함수 (HTML onclick용) ==========
/**
 * HTML onclick에서 사용하는 간단한 래퍼 함수
 */
function copyRecentLogsFromInput() {
    console.log('='.repeat(50));
    console.log('[DEBUG] copyRecentLogsFromInput 호출됨');
    console.log('[DEBUG] typeof copyRecentLogsFromInput:', typeof copyRecentLogsFromInput);
    console.log('[DEBUG] window.copyRecentLogsFromInput:', window.copyRecentLogsFromInput);
    
    const input = document.getElementById('custom-log-lines');
    console.log('[DEBUG] input 요소:', input);
    console.log('[DEBUG] input.value:', input?.value);
    
    const lines = parseInt(input?.value || 200);
    console.log('[DEBUG] 복사할 줄 수:', lines);
    console.log('[DEBUG] typeof copyRecentLogs:', typeof copyRecentLogs);
    console.log('[DEBUG] window.copyRecentLogs:', window.copyRecentLogs);
    
    console.log('[DEBUG] copyRecentLogs 함수 호출 직전');
    copyRecentLogs(lines);
    console.log('[DEBUG] copyRecentLogs 함수 호출 완료');
    console.log('='.repeat(50));
}

// ========== 전역 함수 노출 (HTML onclick에서 사용) ==========
window.testCopyFunction = testCopyFunction;
window.copyRecentLogs = copyRecentLogs;
window.copyRecentLogsFromInput = copyRecentLogsFromInput;
window.copyAllLogs = copyAllLogs;
window.clearAllLogs = clearAllLogs;
window.showClippingPage = showClippingPage;
window.showCrawlerPage = showCrawlerPage;
window.showClippingDetail = showClippingDetail;
window.closeClippingDetail = closeClippingDetail;
window.addKeyword = addKeyword;
window.removeKeyword = removeKeyword;
window.saveClipping = saveClipping;
window.deleteClipping = deleteClipping;
window.editClipping = editClipping;
window.toggleSelection = toggleSelection;
window.removeFromSelection = removeFromSelection;
