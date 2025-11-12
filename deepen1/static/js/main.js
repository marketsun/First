// 유틸리티 함수
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    
    // body에 직접 추가 (더 안전함)
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('ko-KR');
}

// URL에서 도메인 이름 추출
function extractDomainName(url) {
    try {
        const urlObj = new URL(url);
        let domain = urlObj.hostname;
        
        // www. 제거
        domain = domain.replace(/^www\./, '');
        
        // 최상위 도메인만 추출 (예: naver.com -> naver)
        const parts = domain.split('.');
        if (parts.length > 1) {
            return parts[0].charAt(0).toUpperCase() + parts[0].slice(1);
        }
        return domain;
    } catch (e) {
        return 'Unknown';
    }
}

// 전역 변수: 원본 유튜브 데이터 저장
let originalYoutubeData = [];

// 정렬 상태 관리
let youtubeSortState = {
    date: 'desc',  // 'asc' (오래된순), 'desc' (최신순), null (정렬 없음)
    views: null    // 'asc' (낮은순), 'desc' (높은순), null (정렬 없음)
};

// 업로드 날짜 텍스트를 숫자 점수로 변환 (낮을수록 최신)
function parseUploadDateScore(dateText) {
    if (!dateText) return Infinity; // 날짜 없으면 가장 오래된 것으로 처리
    
    const text = dateText.toLowerCase();
    
    // 숫자 추출
    const numberMatch = text.match(/\d+/);
    if (!numberMatch) return Infinity;
    const number = parseInt(numberMatch[0]);
    
    // 단위별 점수 (초 단위로 환산)
    if (text.includes('초') || text.includes('second')) {
        return number * 1;
    } else if (text.includes('분') || text.includes('minute')) {
        return number * 60;
    } else if (text.includes('시간') || text.includes('hour')) {
        return number * 3600;
    } else if (text.includes('일') || text.includes('day')) {
        return number * 86400;
    } else if (text.includes('주') || text.includes('week')) {
        return number * 604800;
    } else if (text.includes('개월') || text.includes('month')) {
        return number * 2592000;
    } else if (text.includes('년') || text.includes('year')) {
        return number * 31536000;
    }
    
    return Infinity;
}

// 정렬 토글 함수
function toggleYoutubeSort(column) {
    if (column === 'date') {
        // 업로드일 정렬 토글: desc → asc → null → desc
        if (youtubeSortState.date === 'desc') {
            youtubeSortState.date = 'asc';
        } else if (youtubeSortState.date === 'asc') {
            youtubeSortState.date = null;
        } else {
            youtubeSortState.date = 'desc';
        }
    } else if (column === 'views') {
        // 조회수 정렬 토글: null → desc → asc → null
        if (youtubeSortState.views === null) {
            youtubeSortState.views = 'desc';
        } else if (youtubeSortState.views === 'desc') {
            youtubeSortState.views = 'asc';
        } else {
            youtubeSortState.views = null;
        }
    }
    
    applyYoutubeFilters();
}

// 유튜브 필터 적용
function applyYoutubeFilters() {
    if (originalYoutubeData.length === 0) {
        return;
    }
    
    // 데이터 복사
    let filteredData = [...originalYoutubeData];
    
    // 복합 정렬 (업로드일 + 조회수)
    filteredData.sort((a, b) => {
        // 1차 정렬: 업로드일
        let dateComparison = 0;
        if (youtubeSortState.date) {
            const dateScoreA = parseUploadDateScore(a.upload_date);
            const dateScoreB = parseUploadDateScore(b.upload_date);
            
            if (youtubeSortState.date === 'desc') {
                // 최신순 (점수 낮은 순)
                dateComparison = dateScoreA - dateScoreB;
            } else if (youtubeSortState.date === 'asc') {
                // 오래된순 (점수 높은 순)
                dateComparison = dateScoreB - dateScoreA;
            }
        }
        
        // 날짜가 다르면 날짜 기준으로 정렬
        if (dateComparison !== 0) {
            return dateComparison;
        }
        
        // 2차 정렬: 조회수
        if (youtubeSortState.views) {
            const viewsA = a.view_count_numeric || 0;
            const viewsB = b.view_count_numeric || 0;
            
            if (youtubeSortState.views === 'desc') {
                // 높은순
                return viewsB - viewsA;
            } else if (youtubeSortState.views === 'asc') {
                // 낮은순
                return viewsA - viewsB;
            }
        }
        
        return 0;
    });
    
    // 결과 렌더링
    renderYoutubeResults(filteredData);
}

// 유튜브 결과 렌더링 함수
function renderYoutubeResults(data) {
    const youtubeResults = document.getElementById('youtube-results');
    const youtubeCount = document.getElementById('youtube-count');
    
    if (data.length > 0) {
        // 정렬 아이콘 생성
        const getDateSortIcon = () => {
            if (youtubeSortState.date === 'desc') return '<span class="sort-icon active">↓</span><span class="sort-icon">↑</span>';
            if (youtubeSortState.date === 'asc') return '<span class="sort-icon">↓</span><span class="sort-icon active">↑</span>';
            return '<span class="sort-icon">↓</span><span class="sort-icon">↑</span>';
        };
        
        const getViewsSortIcon = () => {
            if (youtubeSortState.views === 'desc') return '<span class="sort-icon active">↓</span><span class="sort-icon">↑</span>';
            if (youtubeSortState.views === 'asc') return '<span class="sort-icon">↓</span><span class="sort-icon active">↑</span>';
            return '<span class="sort-icon">↓</span><span class="sort-icon">↑</span>';
        };
        
        // 표시용 순서 번호 계산
        let displayPosition = 1;
        
        youtubeResults.innerHTML = `
            <div class="result-table">
                <div class="result-table-header">
                    <div class="result-table-cell" style="width: 60px;">순서</div>
                    <div class="result-table-cell" style="width: 100px;">타입</div>
                    <div class="result-table-cell channel-cell">채널명</div>
                    <div class="result-table-cell date-cell sortable" onclick="toggleYoutubeSort('date')">
                        업로드일 ${getDateSortIcon()}
                    </div>
                    <div class="result-table-cell views-cell sortable" onclick="toggleYoutubeSort('views')">
                        조회수 ${getViewsSortIcon()}
                    </div>
                    <div class="result-table-cell title-cell">제목</div>
                </div>
                ${data.map(result => {
                    const typeLabel = result.is_short 
                        ? `숏츠${result.short_shelf_index}-${result.position_in_shelf}`
                        : '일반';
                    const typeStyle = result.is_short ? 'color: #FF0000; font-weight: bold;' : '';
                    
                    // 순서 번호 결정
                    let positionText = '';
                    if (result.is_short) {
                        // Shorts의 첫 번째만 순서 표시
                        if (result.position_in_shelf === 1) {
                            positionText = displayPosition;
                            displayPosition++;
                        } else {
                            positionText = ''; // 공백
                        }
                    } else {
                        // 일반 영상은 항상 순서 표시
                        positionText = displayPosition;
                        displayPosition++;
                    }
                    
                    return `
                        <div class="result-table-row">
                            <div class="result-table-cell" style="width: 60px; text-align: center;">${positionText}</div>
                            <div class="result-table-cell" style="width: 100px; ${typeStyle}">${typeLabel}</div>
                            <div class="result-table-cell channel-cell">${result.channel_name || '-'}</div>
                            <div class="result-table-cell date-cell">${result.upload_date || '-'}</div>
                            <div class="result-table-cell views-cell">${result.view_count || '-'}</div>
                            <div class="result-table-cell title-cell">
                                <a href="${result.url}" target="_blank">${result.title}</a>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
        youtubeCount.textContent = data.length;
    } else {
        youtubeResults.innerHTML = `
            <div class="result-table">
                <div class="result-table-header">
                    <div class="result-table-cell" style="width: 60px;">순서</div>
                    <div class="result-table-cell" style="width: 100px;">타입</div>
                    <div class="result-table-cell channel-cell">채널명</div>
                    <div class="result-table-cell date-cell sortable" onclick="toggleYoutubeSort('date')">
                        업로드일 <span class="sort-icon">↓</span><span class="sort-icon">↑</span>
                    </div>
                    <div class="result-table-cell views-cell sortable" onclick="toggleYoutubeSort('views')">
                        조회수 <span class="sort-icon">↓</span><span class="sort-icon">↑</span>
                    </div>
                    <div class="result-table-cell title-cell">제목</div>
                </div>
                <div class="empty-state"><div class="empty-state-icon">🔍</div><div class="empty-state-text">검색 결과가 없습니다.</div></div>
            </div>
        `;
        youtubeCount.textContent = '0';
    }
}

// 검색 기능
async function performSearch(keyword) {
    const progressContainer = document.getElementById('progress-container');
    const progressFill = document.getElementById('progress-fill');
    const statusMessage = document.getElementById('status-message');
    const searchBtn = document.getElementById('search-btn');
    
    // UI 업데이트
    progressContainer.style.display = 'block';
    searchBtn.disabled = true;
    progressFill.style.width = '0%';
    progressFill.textContent = '0%';
    statusMessage.textContent = '크롤링을 시작합니다...';
    
    try {
        // 검색 요청
        const response = await fetch('/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ keyword })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || '검색 중 오류가 발생했습니다.');
        }
        
        const crawlId = data.crawl_id;
        
        // 진행 상태 확인
        const checkStatus = setInterval(async () => {
            try {
                const statusResponse = await fetch(`/crawl-status/${crawlId}`);
                const statusData = await statusResponse.json();
                
                // 진행률 업데이트
                const progress = statusData.progress || 0;
                progressFill.style.width = `${progress}%`;
                progressFill.textContent = `${progress}%`;
                
                if (statusData.status === 'completed') {
                    clearInterval(checkStatus);
                    statusMessage.textContent = '크롤링이 완료되었습니다!';
                    showAlert('검색이 완료되었습니다!', 'success');
                    
                    // 결과 페이지로 이동
                    setTimeout(() => {
                        window.location.href = `/results/${statusData.search_id}`;
                    }, 1000);
                    
                } else if (statusData.status === 'error') {
                    clearInterval(checkStatus);
                    statusMessage.textContent = '오류가 발생했습니다.';
                    showAlert(statusData.error || '크롤링 중 오류가 발생했습니다.', 'error');
                    searchBtn.disabled = false;
                    
                } else if (statusData.status === 'running') {
                    if (progress < 30) {
                        statusMessage.textContent = '구글 검색 중...';
                    } else if (progress < 60) {
                        statusMessage.textContent = '유튜브 검색 중...';
                    } else {
                        statusMessage.textContent = '결과를 저장하는 중...';
                    }
                }
                
            } catch (error) {
                console.error('상태 확인 오류:', error);
            }
        }, 1000);
        
    } catch (error) {
        showAlert(error.message, 'error');
        searchBtn.disabled = false;
        progressContainer.style.display = 'none';
    }
}

// 결과 로드 및 필터링
async function loadResults(searchId, filters = {}) {
    const googleResults = document.getElementById('google-results');
    const youtubeResults = document.getElementById('youtube-results');
    const googleCount = document.getElementById('google-count');
    const youtubeCount = document.getElementById('youtube-count');
    
    // 로딩 표시
    googleResults.innerHTML = '<div class="loading"><div class="spinner"></div><p>로딩 중...</p></div>';
    youtubeResults.innerHTML = '<div class="loading"><div class="spinner"></div><p>로딩 중...</p></div>';
    
    try {
        // 필터 파라미터 생성
        const params = new URLSearchParams(filters);
        
        const response = await fetch(`/api/results/${searchId}?${params}`);
        const data = await response.json();
        
        // 구글 결과 렌더링 (테이블 형식)
        if (data.google_results.length > 0) {
            googleResults.innerHTML = `
                <div class="result-table">
                    <div class="result-table-header">
                        <div class="result-table-cell source-cell">출처</div>
                        <div class="result-table-cell title-cell">제목</div>
                    </div>
                    ${data.google_results.map(result => `
                        <div class="result-table-row">
                            <div class="result-table-cell source-cell">${extractDomainName(result.url)}</div>
                            <div class="result-table-cell title-cell">
                                <a href="${result.url}" target="_blank">${result.title}</a>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
            googleCount.textContent = data.google_results.length;
        } else {
            googleResults.innerHTML = `
                <div class="result-table">
                    <div class="result-table-header">
                        <div class="result-table-cell source-cell">출처</div>
                        <div class="result-table-cell title-cell">제목</div>
                    </div>
                    <div class="empty-state"><div class="empty-state-icon">🔍</div><div class="empty-state-text">검색 결과가 없습니다.</div></div>
                </div>
            `;
            googleCount.textContent = '0';
        }
        
        // 유튜브 결과 저장 및 렌더링
        originalYoutubeData = data.youtube_results;
        renderYoutubeResults(originalYoutubeData);
        
    } catch (error) {
        console.error('결과 로드 오류:', error);
        showAlert('결과를 불러오는 중 오류가 발생했습니다.', 'error');
    }
}

// 검색 기록 로드
async function loadHistory() {
    const historyList = document.getElementById('history-list');
    
    historyList.innerHTML = '<div class="loading"><div class="spinner"></div><p>로딩 중...</p></div>';
    
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        
        if (data.length > 0) {
            historyList.innerHTML = data.map(search => `
                <div class="history-item">
                    <div class="history-info">
                        <div class="history-keyword">${search.keyword}</div>
                        <div class="history-date">${formatDate(search.search_date)}</div>
                    </div>
                    <div class="history-stats">
                        <div class="stat-item">
                            <div class="stat-value">${search.google_count}</div>
                            <div class="stat-label">구글</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${search.youtube_count}</div>
                            <div class="stat-label">유튜브</div>
                        </div>
                    </div>
                    <div class="history-actions">
                        <button class="btn btn-primary btn-small" onclick="window.location.href='/results/${search.id}'">보기</button>
                        <button class="btn btn-danger btn-small" onclick="deleteHistory(${search.id})">삭제</button>
                    </div>
                </div>
            `).join('');
        } else {
            historyList.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📋</div><div class="empty-state-text">검색 기록이 없습니다.</div></div>';
        }
        
    } catch (error) {
        console.error('기록 로드 오류:', error);
        showAlert('검색 기록을 불러오는 중 오류가 발생했습니다.', 'error');
    }
}

// 검색 기록 삭제
async function deleteHistory(searchId) {
    if (!confirm('이 검색 기록을 삭제하시겠습니까?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/history/${searchId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showAlert('삭제되었습니다.', 'success');
            loadHistory();
        } else {
            throw new Error('삭제 실패');
        }
        
    } catch (error) {
        console.error('삭제 오류:', error);
        showAlert('삭제 중 오류가 발생했습니다.', 'error');
    }
}

// 필터 적용
function applyFilters(searchId) {
    const filters = {
        keyword: document.getElementById('filter-keyword')?.value || '',
        date_from: document.getElementById('filter-date-from')?.value || '',
        date_to: document.getElementById('filter-date-to')?.value || '',
        sort_by: document.getElementById('filter-sort')?.value || ''
    };
    
    loadResults(searchId, filters);
}

// 필터 초기화
function resetFilters(searchId) {
    document.getElementById('filter-keyword').value = '';
    document.getElementById('filter-date-from').value = '';
    document.getElementById('filter-date-to').value = '';
    document.getElementById('filter-sort').value = '';
    
    loadResults(searchId);
}


