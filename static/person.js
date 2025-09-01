// Socket.IO 연결 변수
let socket = null;
let isSocketConnected = false;

// Socket.IO를 페이지 로드 즉시 초기화
if (typeof io !== 'undefined') {
  socket = io();
  
  socket.on('connect', function() {
    console.log('Socket.IO connected immediately');
    isSocketConnected = true;
    
    // 분석 세션 참여
    socket.emit('join_analysis', { session_id: socket.id });
  });
  
  socket.on('disconnect', function() {
    console.log('Socket.IO disconnected');
    isSocketConnected = false;
  });
  
  // 실시간 진행 상황 업데이트
  socket.on('analysis_progress', function(data) {
    console.log('Analysis progress:', data);
    updateAnalysisStepRealtime(data.step, data.progress, data.message);
  });
  
  // LLM 스트리밍 응답
  socket.on('llm_response', function(data) {
    console.log('LLM response:', data);
    updateLLMResponse(data);
  });
} else {
  console.log('Socket.IO not available');
}

window.addEventListener("DOMContentLoaded", () => {
  // 페이지 새로고침 시 초기화 처리
  handlePageRefresh();
  
  // 물이 차오르는 컵 애니메이션
  document.querySelectorAll('.water-glass').forEach(el => {
    const pct = parseFloat(el.dataset.percent || '0');
    const p = Math.max(0, Math.min(100, pct)); // 0~100
    el.style.setProperty('--p', p + '%');
    
    // 물 채우기 애니메이션
    const waterFill = el.querySelector('.water-fill');
    if (waterFill) {
      setTimeout(() => {
        waterFill.style.height = p + '%';
      }, 500);
    }
  });
  
  // 프로그레스 바 폭 애니메이션 width 변수 주입
  document.querySelectorAll('.bar span').forEach(span => {
    const style = span.getAttribute('style');
    const m = /width:\s*([0-9.]+)%/.exec(style||'');
    if (m) span.style.setProperty('--w', m[1] + '%');
  });

  // Dropzone 기능
  initDropzone();
  
  // 폼 제출 시 진행 상황 표시
  initProgressTracking();
  
  // 사람 모양 차트 애니메이션
  initHumanCharts();
  
  // 분석 확인 기능 초기화
  initAnalysisConfirmation();
  
  // 이미지 갤러리 슬라이더
  initImageGallery();
});

function initDropzone() {
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('images');
  const fileList = document.getElementById('file-list');
  const filesContainer = document.getElementById('files');
  const analyzeBtn = document.getElementById('analyze-btn');
  
  if (!dropzone || !fileInput) return;
  
  let selectedFiles = [];

  // 파일 입력 변경 이벤트
  fileInput.addEventListener('change', handleFiles);
  
  // 드롭존 클릭 이벤트
  dropzone.addEventListener('click', () => {
    fileInput.click();
  });

  // 드래그 이벤트
  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
  });

  dropzone.addEventListener('dragleave', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
  });

  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    
    const files = Array.from(e.dataTransfer.files);
    const imageFiles = files.filter(file => file.type.startsWith('image/'));
    
    if (imageFiles.length > 0) {
      addFiles(imageFiles);
    }
  });

  function handleFiles(e) {
    const files = Array.from(e.target.files);
    addFiles(files);
  }

  function addFiles(files) {
    files.forEach(file => {
      if (!selectedFiles.find(f => f.name === file.name && f.size === file.size)) {
        selectedFiles.push(file);
      }
    });
    updateFileList();
    updateAnalyzeButton();
  }

  function removeFile(index) {
    selectedFiles.splice(index, 1);
    updateFileList();
    updateAnalyzeButton();
    updateFileInput();
  }

  function updateFileList() {
    if (selectedFiles.length === 0) {
      fileList.style.display = 'none';
      return;
    }

    fileList.style.display = 'block';
    filesContainer.innerHTML = '';

    selectedFiles.forEach((file, index) => {
      const fileItem = document.createElement('div');
      fileItem.className = 'file-item';
      fileItem.innerHTML = `
        <span class="file-name" title="${file.name}">📄 ${file.name}</span>
        <span class="file-remove" onclick="removeFileAtIndex(${index})" title="제거">×</span>
      `;
      filesContainer.appendChild(fileItem);
    });
  }

  function updateAnalyzeButton() {
    analyzeBtn.disabled = selectedFiles.length === 0;
  }

  function updateFileInput() {
    // FileList는 읽기 전용이므로 DataTransfer를 사용
    const dt = new DataTransfer();
    selectedFiles.forEach(file => dt.items.add(file));
    fileInput.files = dt.files;
  }

  // 전역 함수로 등록 (HTML onclick에서 호출하기 위해)
  window.removeFileAtIndex = removeFile;
}

// 물컵 차트 애니메이션
function initHumanCharts() {
  document.querySelectorAll('.water-glass').forEach(glass => {
    const percent = parseFloat(glass.dataset.percent || 0);
    const fillHeight = Math.min(Math.max(percent, 0), 100);
    
    // CSS 변수로 채움 높이 설정
    glass.style.setProperty('--fill-height', `${fillHeight}%`);
  });
}

// 상세 분석 단계 진행 상황 업데이트
function updateAnalysisStep(stepId, progress = 0, message = '') {
  console.log('updateAnalysisStep called:', stepId, progress, message);
  
  const steps = ['step-upload', 'step-ocr', 'step-nutrition', 'step-recommendation', 'step-complete'];
  const currentIndex = steps.indexOf(stepId);
  
  // 전체 진행률 계산 (각 단계별 20%)
  const overallProgress = Math.min(100, (currentIndex * 20) + (progress * 0.2));
  
  // 전체 진행 바 업데이트
  const overallProgressBar = document.getElementById('progress-bar');
  const overallProgressText = document.getElementById('progress-percentage');
  const overallProgressSummary = document.getElementById('progress-summary');
  
  if (overallProgressBar) {
    overallProgressBar.style.width = `${overallProgress}%`;
  }
  if (overallProgressText) {
    overallProgressText.textContent = `${Math.round(overallProgress)}%`;
  }
  if (overallProgressSummary) {
    overallProgressSummary.textContent = `${Math.round(overallProgress)}%`;
  }
  
  // 각 단계별 상태 업데이트
  steps.forEach((step, index) => {
    const element = document.getElementById(step);
    const statusElement = document.getElementById(`status-${step.replace('step-', '')}`);
    const progressFill = document.getElementById(`progress-${step.replace('step-', '')}`);
    const progressText = document.getElementById(`progress-text-${step.replace('step-', '')}`);
    
    if (element) {
      element.classList.remove('active', 'completed');
      
      if (index < currentIndex) {
        // 완료된 단계
        element.classList.add('completed');
        if (statusElement) statusElement.textContent = '✅';
        if (progressFill) progressFill.style.width = '100%';
        if (progressText) progressText.textContent = '완료';
      } else if (index === currentIndex) {
        // 현재 진행중인 단계
        element.classList.add('active');
        if (statusElement) statusElement.textContent = '🔄';
        if (progressFill) progressFill.style.width = `${progress}%`;
        if (progressText) progressText.textContent = message || `${progress}%`;
      } else {
        // 대기중인 단계
        if (statusElement) statusElement.textContent = '⏳';
        if (progressFill) progressFill.style.width = '0%';
        if (progressText) progressText.textContent = '대기중...';
      }
    }
  });
  
  // 로딩 텍스트 업데이트
  const loadingText = document.getElementById('loading-text');
  if (loadingText) {
    const stepNames = {
      'step-upload': '파일 업로드 중...',
      'step-ocr': 'OCR 분석 중...',
      'step-nutrition': '영양정보 추출 중...',
      'step-recommendation': 'AI 추천 생성 중...',
      'step-complete': '분석 완료!'
    };
    loadingText.textContent = stepNames[stepId] || '분석 중...';
  }
}

function initProgressTracking() {
  const form = document.getElementById('upload-form');
  const progressContainer = document.getElementById('progress-container');
  const analyzeBtn = document.getElementById('analyze-btn');
  
  if (!form) {
    console.log('Upload form not found');
    return;
  }
  
  console.log('Progress tracking initialized');
  
  form.addEventListener('submit', function(e) {
    console.log('Form submit event triggered');
    const fileInput = document.getElementById('images');
    const files = Array.from(fileInput.files);
    
    if (files.length === 0) {
      console.log('No files selected, not showing progress');
      return;
    }
    
    console.log('Showing progress for', files.length, 'files');
    
    // 분석 시작 플래그 설정
    sessionStorage.setItem('isFromAnalysis', 'true');
    
    // 진행 상황 UI 표시
    if (progressContainer) {
    progressContainer.style.display = 'block';
      console.log('Progress container displayed');
    } else {
      console.log('Progress container not found');
    }
    
    if (analyzeBtn) {
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = '분석 중...';
    }
    
    // 기존 결과 섹션 숨기기
    hideExistingResults();
    
    // Socket.IO 연결 확인 후 적절한 방법 선택
    if (socket && isSocketConnected) {
      // 웹소켓 연결이 있으면 백엔드에서 진행 상황 처리
      console.log('Form submitted, Socket.IO will handle progress');
      // 백엔드에서 자동으로 진행 상황을 전송할 것임
    } else {
      // 웹소켓이 없으면 클라이언트 시뮬레이션 사용
      console.log('Form submitted, using client simulation');
      simulateFileUploadProgress(files, () => {
        simulateRealisticProgress(files);
      });
    }
  });
}

// 실시간 진행 상황 업데이트 (Socket.IO 기반)
function updateAnalysisStepRealtime(step, progress, message) {
  console.log('Real-time progress update:', step, progress, message);
  
  const stepMap = {
    'upload': 'step-upload',
    'ocr': 'step-ocr', 
    'nutrition': 'step-nutrition',
    'recommendation': 'step-recommendation',
    'complete': 'step-complete'
  };
  
  const stepId = stepMap[step] || step;
  updateAnalysisStep(stepId, progress, message);
  
  // 분석 완료 시 매끄러운 화면 전환
  if (step === 'complete' && progress === 100) {
    handleAnalysisComplete();
  }
}

// 분석 완료 처리 함수
function handleAnalysisComplete() {
  console.log('Analysis completed, transitioning to results...');
  
  const progressContainer = document.getElementById('progress-container');
  const analyzeBtn = document.getElementById('analyze-btn');
  
  // 2초 후 진행 상황 숨기고 결과 화면으로 전환
  setTimeout(() => {
    // 진행 상황 패널을 부드럽게 숨김
    if (progressContainer) {
      progressContainer.style.transition = 'opacity 0.5s ease-out, transform 0.5s ease-out';
      progressContainer.style.opacity = '0';
      progressContainer.style.transform = 'translateY(-20px)';
      
      setTimeout(() => {
        progressContainer.style.display = 'none';
        // 결과 섹션을 부드럽게 표시
        showResultsWithAnimation();
      }, 500);
    }
    
    // 버튼 상태 복원
    if (analyzeBtn) {
      analyzeBtn.disabled = false;
      analyzeBtn.textContent = '영양정보 분석';
      analyzeBtn.style.transition = 'all 0.3s ease';
    }
  }, 2000); // 2초 대기
}

// 기존 결과 섹션 숨기기
function hideExistingResults() {
  const resultsSection = document.querySelector('.results');
  if (resultsSection) {
    console.log('Hiding existing results section');
    resultsSection.style.transition = 'opacity 0.5s ease-out, transform 0.5s ease-out';
    resultsSection.style.opacity = '0';
    resultsSection.style.transform = 'translateY(-20px)';
    
    setTimeout(() => {
      resultsSection.style.display = 'none';
    }, 500);
  }
}

// 결과 화면을 애니메이션과 함께 표시
function showResultsWithAnimation() {
  // 결과가 없는 경우 페이지 새로고침으로 결과 표시
  console.log('Analysis completed, reloading page to show results...');
  
  // 분석 완료 플래그 설정
  sessionStorage.setItem('isFromAnalysis', 'true');
  
  // 부드러운 전환을 위해 약간 대기 후 새로고침
  setTimeout(() => {
    window.location.reload();
  }, 500);
}

// LLM 스트리밍 응답 처리
function updateLLMResponse(data) {
  const { type, data: content, full_response } = data;
  
  console.log('LLM Response received:', { type, content, full_response });
  
  if (type === 'thinking' || type === 'connecting' || type === 'generating' || type === 'responding') {
    // 진행 상태 메시지 표시 (채팅 스타일)
    updateRecommendationText(createTypingIndicator(content), false, true);
  } else if (type === 'chunk') {
    // 실시간으로 텍스트 추가
    updateRecommendationText(full_response || content, false);
  } else if (type === 'complete') {
    // 완료된 응답 표시
    updateRecommendationText(full_response || content, true);
    updateAnalysisStep('step-complete', 100, '모든 분석이 완료되었습니다!');
    
    // 매끄러운 화면 전환
    handleAnalysisComplete();
  } else if (type === 'error') {
    console.error('LLM Error:', content);
    updateRecommendationText(`❌ ${content}`, true);
  }
}

// 타이핑 인디케이터 생성 (채팅 스타일)
function createTypingIndicator(message) {
  return `
    <div class="llm-typing-container">
      <div class="llm-status-message">${message}</div>
      <div class="llm-typing-dots">
        <span class="dot"></span>
        <span class="dot"></span>
        <span class="dot"></span>
      </div>
    </div>
  `;
}

// 추천 텍스트 업데이트
function updateRecommendationText(content, isComplete, isTyping = false) {
  const maleRecommendationElement = document.querySelector('#male-recommendation .recommendation-content-text');
  const femaleRecommendationElement = document.querySelector('#female-recommendation .recommendation-content-text');
  
  if (maleRecommendationElement) {
    if (isTyping) {
      // 타이핑 인디케이터는 HTML 그대로 표시
      maleRecommendationElement.innerHTML = content;
    } else if (isComplete) {
      maleRecommendationElement.innerHTML = content.replace(/\n/g, '<br>');
    } else {
      maleRecommendationElement.innerHTML += content.replace(/\n/g, '<br>');
    }
  }
  
  if (femaleRecommendationElement) {
    if (isTyping) {
      // 타이핑 인디케이터는 HTML 그대로 표시
      femaleRecommendationElement.innerHTML = content;
    } else if (isComplete) {
      femaleRecommendationElement.innerHTML = content.replace(/\n/g, '<br>');
    } else {
      femaleRecommendationElement.innerHTML += content.replace(/\n/g, '<br>');
    }
  }
}

// 파일 업로드 진행 상황 시뮬레이션
function simulateFileUploadProgress(files, callback) {
  console.log('Simulating file upload progress for', files.length, 'files');
  
  // 파일 업로드 시작
  updateAnalysisStep('step-upload', 0, '파일 업로드 시작...');
  
  let progress = 0;
  const totalFiles = files.length;
  let currentFileIndex = 0;
  
  const uploadInterval = setInterval(() => {
    progress += 5; // 5%씩 증가
    
    if (progress >= 100) {
      progress = 100;
      updateAnalysisStep('step-upload', 100, `${totalFiles}개 파일 업로드 완료`);
      clearInterval(uploadInterval);
      
      // 업로드 완료 후 콜백 실행
      setTimeout(() => {
        if (callback) callback();
      }, 500);
    } else {
      // 현재 파일 정보 업데이트
      const currentFileProgress = (progress / 100) * totalFiles;
      currentFileIndex = Math.floor(currentFileProgress);
      
      const currentFileName = files[Math.min(currentFileIndex, totalFiles - 1)]?.name || 'file';
      updateAnalysisStep('step-upload', progress, `업로드 중: ${currentFileName} (${currentFileIndex + 1}/${totalFiles})`);
    }
  }, 100); // 100ms마다 업데이트 (더 부드러운 진행)
}

// 실제 처리 과정과 동기화된 진행 시뮬레이션 함수
function simulateRealisticProgress(files) {
  const fileCount = files.length;
  
  console.log('Starting realistic progress simulation for', fileCount, 'files');
  
  // 파일 업로드는 이미 완료된 상태로 시작 (simulateFileUploadProgress에서 처리)
  
  // 2단계: OCR 분석 (파일당 실제 시간 추정)
  setTimeout(() => {
    updateAnalysisStep('step-ocr', 0, 'OCR 분석 시작...');
    
    // 실제 OCR 처리 시간을 시뮬레이션 (파일당 2-4초)
    const ocrDuration = fileCount * 2500; // 파일당 2.5초 기준
    let ocrProgress = 0;
    let currentFileIndex = 0;
    
    const ocrInterval = setInterval(() => {
      ocrProgress += (100 / (ocrDuration / 200)); // 200ms마다 업데이트
      currentFileIndex = Math.floor((ocrProgress / 100) * fileCount);
      
      if (ocrProgress >= 100) {
        ocrProgress = 100;
        clearInterval(ocrInterval);
        updateAnalysisStep('step-ocr', 100, `${fileCount}개 파일 OCR 완료`);
        
        // 3단계: 영양정보 추출 (실제 파싱 시간)
        setTimeout(() => {
          updateAnalysisStep('step-nutrition', 0, '영양정보 파싱 시작...');
          
          // 영양정보 추출은 빠름 (1초)
          setTimeout(() => {
            updateAnalysisStep('step-nutrition', 50, '영양성분 계산 중...');
            
            setTimeout(() => {
              updateAnalysisStep('step-nutrition', 100, '영양정보 추출 완료');
              
              // 4단계: AI 추천 생성 (LLM API 호출 시간)
              setTimeout(() => {
                updateAnalysisStep('step-recommendation', 0, 'LLM API 호출...');
                
                // LLM 호출은 시간이 오래 걸림 (5-10초)
                let llmProgress = 0;
                const llmInterval = setInterval(() => {
                  llmProgress += Math.random() * 8 + 2; // 2-10씩 증가
                  
                  if (llmProgress >= 100) {
                    llmProgress = 100;
                    clearInterval(llmInterval);
                    updateAnalysisStep('step-recommendation', 100, 'AI 추천 완료');
                    
                    // 5단계: 완료
                    setTimeout(() => {
                      updateAnalysisStep('step-complete', 100, '모든 분석 완료!');
                      
                      // 매끄러운 화면 전환
                      handleAnalysisComplete();
                    }, 300);
                    
                  } else {
                    const messages = [
                      'AI 모델 로딩...',
                      '부족 영양소 분석...',
                      '맞춤형 추천 생성...',
                      '결과 검증 중...'
                    ];
                    const messageIndex = Math.floor((llmProgress / 100) * messages.length);
                    updateAnalysisStep('step-recommendation', Math.round(llmProgress), messages[Math.min(messageIndex, messages.length - 1)]);
                  }
                }, 500); // 500ms마다 업데이트
                
              }, 300);
            }, 500);
          }, 500);
        }, 200);
        
      } else {
        const currentFile = Math.min(currentFileIndex + 1, fileCount);
        updateAnalysisStep('step-ocr', Math.round(ocrProgress), `이미지 ${currentFile}/${fileCount} 분석 중...`);
      }
    }, 200);
    
  }, 100);
}

function simulateProgress(files) {
  const progressSummary = document.getElementById('progress-summary');
  const progressBar = document.getElementById('progress-bar');
  let currentIndex = 0;
  
  function updateProgress() {
    if (currentIndex < files.length) {
      const item = document.getElementById(`progress-item-${currentIndex}`);
      const statusIcon = item.querySelector('.progress-status');
      const statusText = item.querySelector('.progress-text');
      
      // 현재 파일 처리 중으로 변경
      item.className = 'progress-item current';
      statusIcon.textContent = '🔄';
      statusText.textContent = 'OCR 분석 중...';
      
      // 분석 단계 업데이트
      const steps = ['step-ocr', 'step-nutrition', 'step-recommendation'];
      const stepIndex = Math.min(currentIndex, steps.length - 1);
      updateAnalysisStep(steps[stepIndex]);
      
      // 이전 파일들을 완료로 표시
      for (let i = 0; i < currentIndex; i++) {
        const prevItem = document.getElementById(`progress-item-${i}`);
        prevItem.className = 'progress-item completed';
        prevItem.querySelector('.progress-status').textContent = '✅';
        prevItem.querySelector('.progress-text').textContent = '완료';
      }
      
      // 진행률 업데이트
      const progress = ((currentIndex + 0.5) / files.length) * 100;
      progressBar.style.width = `${progress}%`;
      progressSummary.textContent = `${currentIndex}/${files.length} 완료`;
      
      currentIndex++;
      
      // 다음 파일 처리 (실제로는 서버 응답을 기다림)
      setTimeout(updateProgress, 1000 + Math.random() * 2000);
    } else {
      // 모든 파일 완료
      updateAnalysisStep('step-complete');
      
      for (let i = 0; i < files.length; i++) {
        const item = document.getElementById(`progress-item-${i}`);
        item.className = 'progress-item completed';
        item.querySelector('.progress-status').textContent = '✅';
        item.querySelector('.progress-text').textContent = '완료';
      }
      
      progressBar.style.width = '100%';
      progressSummary.textContent = `${files.length}/${files.length} 완료`;
    }
  }
  
  // 첫 번째 파일부터 시작
  setTimeout(updateProgress, 500);
}

// 이미지 갤러리 슬라이더
function initImageGallery() {
  const galleryTrack = document.getElementById('gallery-track');
  const prevBtn = document.getElementById('gallery-prev');
  const nextBtn = document.getElementById('gallery-next');
  const indicators = document.querySelectorAll('.gallery-indicators .indicator');
  
  if (!galleryTrack) {
    console.log('Gallery track not found - no results available');
    return;
  }
  
  console.log('Initializing image gallery with', galleryTrack.querySelectorAll('.gallery-item').length, 'items');
  
  const items = galleryTrack.querySelectorAll('.gallery-item');
  const itemWidth = 216; // 200px + 16px gap
  const visibleItems = Math.floor(galleryTrack.parentElement.offsetWidth / itemWidth);
  const maxIndex = Math.max(0, items.length - visibleItems);
  
  let currentIndex = 0;
  let isDragging = false;
  let startX = 0;
  let startTransform = 0;
  
  // 슬라이더 위치 업데이트
  function updateSlider() {
    const translateX = -currentIndex * itemWidth;
    galleryTrack.style.transform = `translateX(${translateX}px)`;
    
    // 네비게이션 버튼 상태 업데이트
    prevBtn.classList.toggle('disabled', currentIndex === 0);
    nextBtn.classList.toggle('disabled', currentIndex >= maxIndex);
    
    // 인디케이터 업데이트
    indicators.forEach((indicator, index) => {
      indicator.classList.toggle('active', 
        index >= currentIndex && index < currentIndex + visibleItems
      );
    });
  }
  
  // 이전/다음 버튼 이벤트
  prevBtn.addEventListener('click', () => {
    if (currentIndex > 0) {
      currentIndex--;
      updateSlider();
    }
  });
  
  nextBtn.addEventListener('click', () => {
    if (currentIndex < maxIndex) {
      currentIndex++;
      updateSlider();
    }
  });
  
  // 인디케이터 클릭 이벤트
  indicators.forEach((indicator, index) => {
    indicator.addEventListener('click', () => {
      currentIndex = Math.min(index, maxIndex);
      updateSlider();
    });
  });
  
  // 마우스 드래그 시작
  galleryTrack.addEventListener('mousedown', (e) => {
    isDragging = true;
    startX = e.clientX;
    startTransform = currentIndex * itemWidth;
    galleryTrack.style.cursor = 'grabbing';
    galleryTrack.style.transition = 'none';
    e.preventDefault();
  });
  
  // 마우스 드래그 중
  document.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    
    const deltaX = e.clientX - startX;
    const newTransform = startTransform - deltaX;
    const maxTransform = maxIndex * itemWidth;
    
    // 경계값 제한
    const clampedTransform = Math.max(0, Math.min(newTransform, maxTransform));
    galleryTrack.style.transform = `translateX(-${clampedTransform}px)`;
  });
  
  // 마우스 드래그 종료
  document.addEventListener('mouseup', (e) => {
    if (!isDragging) return;
    
    isDragging = false;
    galleryTrack.style.cursor = 'grab';
    galleryTrack.style.transition = 'transform 0.5s ease';
    
    const deltaX = e.clientX - startX;
    const threshold = itemWidth / 3;
    
    if (Math.abs(deltaX) > threshold) {
      if (deltaX > 0 && currentIndex > 0) {
        currentIndex--;
      } else if (deltaX < 0 && currentIndex < maxIndex) {
        currentIndex++;
      }
    }
    
    updateSlider();
  });
  
  // 터치 이벤트 (모바일 지원)
  let touchStartX = 0;
  
  galleryTrack.addEventListener('touchstart', (e) => {
    touchStartX = e.touches[0].clientX;
    galleryTrack.style.transition = 'none';
  });
  
  galleryTrack.addEventListener('touchmove', (e) => {
    const touchX = e.touches[0].clientX;
    const deltaX = touchX - touchStartX;
    const newTransform = startTransform - deltaX;
    const maxTransform = maxIndex * itemWidth;
    
    const clampedTransform = Math.max(0, Math.min(newTransform, maxTransform));
    galleryTrack.style.transform = `translateX(-${clampedTransform}px)`;
    e.preventDefault();
  });
  
  galleryTrack.addEventListener('touchend', (e) => {
    const touchEndX = e.changedTouches[0].clientX;
    const deltaX = touchEndX - touchStartX;
    const threshold = itemWidth / 3;
    
    galleryTrack.style.transition = 'transform 0.5s ease';
    
    if (Math.abs(deltaX) > threshold) {
      if (deltaX > 0 && currentIndex > 0) {
        currentIndex--;
      } else if (deltaX < 0 && currentIndex < maxIndex) {
        currentIndex++;
      }
    }
    
    updateSlider();
  });
  
  // 키보드 네비게이션
  document.addEventListener('keydown', (e) => {
    if (e.target.closest('.image-gallery')) {
      if (e.key === 'ArrowLeft' && currentIndex > 0) {
        currentIndex--;
        updateSlider();
      } else if (e.key === 'ArrowRight' && currentIndex < maxIndex) {
        currentIndex++;
        updateSlider();
      }
    }
  });
  
  // 윈도우 리사이즈 시 재계산
  window.addEventListener('resize', () => {
    const newVisibleItems = Math.floor(galleryTrack.parentElement.offsetWidth / itemWidth);
    const newMaxIndex = Math.max(0, items.length - newVisibleItems);
    currentIndex = Math.min(currentIndex, newMaxIndex);
    updateSlider();
  });
  
  // 초기 상태 설정
  galleryTrack.style.cursor = 'grab';
  updateSlider();
  
  // 클릭 이벤트 추가 (onclick 속성 외에 추가 보장)
  const thumbnailContainers = galleryTrack.querySelectorAll('.thumbnail-container');
  console.log('Found thumbnail containers:', thumbnailContainers.length);
  
  thumbnailContainers.forEach((container, index) => {
    console.log(`Setting up click handler for thumbnail ${index}`);
    
    container.addEventListener('click', function(e) {
      console.log('Thumbnail clicked!', index);
      e.preventDefault();
      e.stopPropagation();
      
      // 새로운 data 속성 기반 함수 사용
      showImageDetailFromData(container);
    });
  });
}

// 이미지 상세보기 (data 속성에서 정보 추출)
function showImageDetailFromData(element) {
  console.log('=== showImageDetailFromData START ===');
  
  const galleryItem = element.closest('.gallery-item');
  if (!galleryItem) {
    console.error('Gallery item not found');
    return;
  }
  
  const filename = galleryItem.getAttribute('data-filename');
  const status = galleryItem.getAttribute('data-status');
  const imageUrl = galleryItem.getAttribute('data-image-url');
  const fieldsStr = galleryItem.getAttribute('data-fields');
  const fullPackageStr = galleryItem.getAttribute('data-full-package');
  const ocrTextsStr = galleryItem.getAttribute('data-ocr-texts');
  
  console.log('Extracted data:', { filename, status, imageUrl, fieldsStr, fullPackageStr, ocrTextsStr });
  
  let fields = null;
  let fullPackage = null;
  let ocrTexts = null;
  
  try {
    fields = fieldsStr && fieldsStr !== '{}' ? JSON.parse(fieldsStr) : null;
  } catch (e) {
    console.warn('Failed to parse fields:', e);
  }
  
  try {
    fullPackage = fullPackageStr && fullPackageStr !== '{}' ? JSON.parse(fullPackageStr) : null;
  } catch (e) {
    console.warn('Failed to parse fullPackage:', e);
  }
  
  try {
    ocrTexts = ocrTextsStr && ocrTextsStr !== '[]' ? JSON.parse(ocrTextsStr) : null;
  } catch (e) {
    console.warn('Failed to parse ocrTexts:', e);
  }
  
  console.log('Parsed data:', { fields, fullPackage, ocrTexts });
  
  showImageDetail(filename, status, imageUrl, fields, fullPackage, ocrTexts);
}

// 이미지 상세보기 (전역 함수)
function showImageDetail(filename, status, imageUrl, fields, fullPackage, ocrTexts) {
  console.log('=== showImageDetail START ===');
  console.log('Parameters:', { filename, status, imageUrl, fields, fullPackage, ocrTexts });
  
  // 기존 모달이 있으면 제거
  const existingModal = document.querySelector('.image-detail-modal');
  if (existingModal) {
    console.log('Removing existing modal');
    existingModal.remove();
  }
  
  const statusText = {
    'success': '분석 완료',
    'pass': '분석 실패 (PASS)',
    'error': '오류 발생'
  };
  
  const statusColor = {
    'success': '#22c55e',
    'pass': '#f59e0b', 
    'error': '#ef4444'
  };
  
  // 간단한 알림으로 상세 정보 표시
  const message = `파일명: ${filename}\n상태: ${statusText[status] || status}`;
  
  // 더 나은 UX를 위해 커스텀 알림 생성
  const modal = document.createElement('div');
  modal.className = 'image-detail-modal';
  modal.innerHTML = `
    <div class="modal-backdrop" onclick="closeImageDetail()">
      <div class="modal-content" onclick="event.stopPropagation()">
        <div class="modal-header">
          <h3>📋 ${filename} - 제품 영양정보</h3>
          <button class="modal-close" onclick="closeImageDetail()">✕</button>
        </div>
        <div class="modal-body">
          <div class="image-preview">
            <div class="image-placeholder">
              ${imageUrl ? 
                `<img src="${imageUrl}" alt="${filename}" class="modal-image" />` : 
                `<div class="image-icon">🖼️</div>`
              }
              <div class="image-title">${filename}</div>
            </div>
          </div>
          <div class="image-info">
            <div class="info-item">
              <span class="info-label">파일명:</span>
              <span class="info-value">${filename}</span>
            </div>
            <div class="info-item">
              <span class="info-label">분석 상태:</span>
              <span class="info-value" style="color: ${statusColor[status]}">${statusText[status] || status}</span>
            </div>
            ${status === 'pass' ? 
              '<div class="info-note">이 이미지는 OCR 분석에 실패하여 영양정보를 추출할 수 없었습니다.</div>' : 
              generateNutritionTable(fields, fullPackage, ocrTexts)
            }
          </div>
        </div>
      </div>
    </div>
  `;
  
  console.log('Appending modal to body');
  document.body.appendChild(modal);
  
  console.log('Modal added to DOM, checking if visible');
  
  // 애니메이션을 위해 다음 프레임에 show 클래스 추가
  requestAnimationFrame(() => {
    console.log('Adding show class to modal');
    modal.classList.add('show');
    
    // 모달이 실제로 보이는지 확인
    setTimeout(() => {
      const isVisible = window.getComputedStyle(modal).visibility !== 'hidden' && 
                       window.getComputedStyle(modal).opacity !== '0';
      console.log('Modal visibility check:', isVisible);
      console.log('Modal styles:', {
        visibility: window.getComputedStyle(modal).visibility,
        opacity: window.getComputedStyle(modal).opacity,
        zIndex: window.getComputedStyle(modal).zIndex
      });
    }, 100);
  });
  
  console.log('=== showImageDetail END ===');
}

// 이미지 상세보기 닫기
function closeImageDetail() {
  const modal = document.querySelector('.image-detail-modal');
  if (modal) {
    modal.classList.remove('show');
    setTimeout(() => {
      modal.remove();
    }, 300);
  }
}

// 전역 함수로 등록
window.showImageDetail = showImageDetail;
window.closeImageDetail = closeImageDetail;

// Flash 메시지 제거 함수
function clearFlashMessages() {
  // DOM에서 flash 메시지 요소들 제거
  const flashMessages = document.querySelectorAll('.flash-message, .alert, [class*="flash"]');
  flashMessages.forEach(msg => {
    msg.style.opacity = '0';
    setTimeout(() => {
      if (msg.parentNode) {
        msg.parentNode.removeChild(msg);
      }
    }, 300);
  });
  
  // 특정 텍스트가 포함된 요소들도 확인
  const allElements = document.querySelectorAll('*');
  allElements.forEach(el => {
    if (el.textContent && el.textContent.includes('지원하지 않는 파일 형식')) {
      el.style.opacity = '0';
      setTimeout(() => {
        if (el.parentNode) {
          el.parentNode.removeChild(el);
        }
      }, 300);
    }
  });
}

// 전역 함수로 등록
window.clearFlashMessages = clearFlashMessages;

// 페이지 새로고침 시 초기화 처리
function handlePageRefresh() {
  console.log('Checking for page refresh initialization...');
  
  // 결과가 있는 페이지인지 확인
  const resultsSection = document.querySelector('.results');
  const hasResults = resultsSection && resultsSection.innerHTML.trim().length > 0;
  
  if (hasResults) {
    console.log('Results found on page load');
    
    // 세션 스토리지를 사용한 새로고침 감지
    const pageLoadTime = Date.now();
    const lastPageLoadTime = sessionStorage.getItem('lastPageLoadTime');
    const isFromAnalysis = sessionStorage.getItem('isFromAnalysis') === 'true';
    const fromReset = new URLSearchParams(window.location.search).get('from_reset');
    
    sessionStorage.setItem('lastPageLoadTime', pageLoadTime.toString());
    
    console.log('Page load info:', {
      lastPageLoadTime,
      isFromAnalysis,
      fromReset,
      timeDiff: lastPageLoadTime ? pageLoadTime - parseInt(lastPageLoadTime) : 0
    });
    
    // from_reset 매개변수가 있으면 정상적인 초기화 후 접근
    if (fromReset === 'true') {
      console.log('Normal access after reset');
      sessionStorage.removeItem('isFromAnalysis');
      
      // URL 정리
      const newUrl = window.location.pathname;
      window.history.replaceState({}, document.title, newUrl);
      return;
    }
    
    // 분석 완료 후가 아닌 상태에서 결과 페이지 접근 시 초기화
    if (!isFromAnalysis) {
      console.log('Direct access to results page without analysis, redirecting to home...');
      
      // 즉시 홈으로 이동
      window.location.href = '/';
      return;
    }
    
    // 새로고침 감지 (같은 세션에서 짧은 시간 간격으로 재로드)
    if (lastPageLoadTime && (pageLoadTime - parseInt(lastPageLoadTime)) < 5000) {
      console.log('Page refresh detected, redirecting to home...');
      
      sessionStorage.removeItem('isFromAnalysis');
      window.location.href = '/';
      return;
    }
    
    console.log('Normal page access with results');
  } else {
    console.log('No results found on page, normal initialization');
    sessionStorage.removeItem('isFromAnalysis');
    
    // URL 정리
    if (window.location.search.includes('from_reset')) {
      const newUrl = window.location.pathname;
      window.history.replaceState({}, document.title, newUrl);
    }
  }
}

// 분석 확인 기능 초기화
function initAnalysisConfirmation() {
  const fileInput = document.getElementById('images');
  const confirmationDiv = document.getElementById('analysis-confirmation');
  const fileCountSpan = document.getElementById('file-count');
  const startBtn = document.getElementById('start-analysis-btn');
  const cancelBtn = document.getElementById('cancel-analysis-btn');
  const analyzeBtn = document.getElementById('analyze-btn');
  const form = document.getElementById('upload-form');
  
  if (!fileInput || !confirmationDiv) return;
  
  // 파일 선택 시 확인 다이얼로그 표시
  fileInput.addEventListener('change', function() {
    const fileCount = this.files.length;
    
    if (fileCount > 0) {
      fileCountSpan.textContent = fileCount;
      confirmationDiv.style.display = 'block';
      analyzeBtn.style.display = 'none'; // 기본 분석 버튼 숨김
    } else {
      confirmationDiv.style.display = 'none';
      analyzeBtn.style.display = 'inline-block';
    }
  });
  
  // 분석 시작 버튼 클릭
  if (startBtn) {
    startBtn.addEventListener('click', function() {
      confirmationDiv.style.display = 'none';
      
      // 진행 상황 표시 시작
      const progressContainer = document.getElementById('progress-container');
      const files = Array.from(fileInput.files);
      
      if (progressContainer && files.length > 0) {
        progressContainer.style.display = 'block';
        analyzeBtn.disabled = true;
        analyzeBtn.textContent = '분석 중...';
        
        // 기존 결과 섹션 숨기기
        hideExistingResults();
        
        // Socket.IO 연결 확인 후 적절한 방법 선택
        if (socket && isSocketConnected) {
          // 웹소켓 연결이 있으면 백엔드 신호만 사용
          console.log('Using Socket.IO for real-time progress');
          const filesData = files.map(file => ({
            name: file.name,
            size: file.size,
            type: file.type
          }));
          
          socket.emit('start_analysis', { files: filesData });
        } else {
          // 웹소켓이 없으면 클라이언트 시뮬레이션 사용
          console.log('Socket.IO not available, using client simulation');
          simulateFileUploadProgress(files, () => {
            simulateRealisticProgress(files);
          });
        }
      }
      
      // 분석 시작 플래그 설정
      sessionStorage.setItem('isFromAnalysis', 'true');
      
      // 폼 제출 (분석 시작)
      if (form) {
        form.submit();
      }
    });
  }
  
  // 취소 버튼 클릭
  if (cancelBtn) {
    cancelBtn.addEventListener('click', function() {
      confirmationDiv.style.display = 'none';
      fileInput.value = ''; // 파일 선택 초기화
      analyzeBtn.style.display = 'inline-block';
      analyzeBtn.disabled = true;
    });
  }
}

// 영양정보 표 생성 함수
function generateNutritionTable(fields, fullPackage, ocrTexts) {
  if (!fields && !fullPackage) {
    return '<div class="info-note">❌ 영양정보를 분석할 수 없습니다.</div>';
  }

  // 영양소 한국어 이름 매핑
  const nutrientNames = {
    'calories_kcal': '칼로리',
    'carbs_g': '탄수화물',
    'protein_g': '단백질',
    'fat_g': '지방',
    'saturated_fat_g': '포화지방',
    'trans_fat_g': '트랜스지방',
    'cholesterol_mg': '콜레스테롤',
    'sodium_mg': '나트륨',
    'potassium_mg': '칼륨',
    'fiber_g': '식이섬유',
    'sugars_g': '당류',
    'calcium_mg': '칼슘',
    'iron_mg': '철분',
    'phosphorus_mg': '인',
    'vitamin_a_ug': '비타민A',
    'thiamine_mg': '티아민',
    'riboflavin_mg': '리보플라빈',
    'niacin_mg': '나이아신',
    'vitamin_c_mg': '비타민C'
  };

  // 단위 매핑
  const units = {
    'calories_kcal': 'kcal',
    'carbs_g': 'g',
    'protein_g': 'g',
    'fat_g': 'g',
    'saturated_fat_g': 'g',
    'trans_fat_g': 'g',
    'cholesterol_mg': 'mg',
    'sodium_mg': 'mg',
    'potassium_mg': 'mg',
    'fiber_g': 'g',
    'sugars_g': 'g',
    'calcium_mg': 'mg',
    'iron_mg': 'mg',
    'phosphorus_mg': 'mg',
    'vitamin_a_ug': 'μg',
    'thiamine_mg': 'mg',
    'riboflavin_mg': 'mg',
    'niacin_mg': 'mg',
    'vitamin_c_mg': 'mg'
  };

  // RDI 정보 (남성 기준으로 일단 표시)
  const rdi = {
    'calories_kcal': 2500,
    'carbs_g': 324,
    'protein_g': 65,
    'fat_g': 83,
    'saturated_fat_g': 28,
    'trans_fat_g': null,
    'cholesterol_mg': 300,
    'sodium_mg': 2000,
    'potassium_mg': 3500,
    'fiber_g': 30,
    'sugars_g': null,
    'calcium_mg': 750,
    'iron_mg': 10,
    'phosphorus_mg': 700,
    'vitamin_a_ug': 800,
    'thiamine_mg': 1.2,
    'riboflavin_mg': 1.4,
    'niacin_mg': 16,
    'vitamin_c_mg': 100
  };

  let tableHTML = `
    <div class="nutrition-analysis">
      <div class="info-note success">✅ 이 이미지에서 영양정보가 성공적으로 분석되었습니다.</div>
      <div class="nutrition-table-container">
        <h4>📊 이 제품의 영양정보</h4>
        <div class="table-description">
          <small>아래는 현재 선택된 이미지에서 추출한 개별 제품의 영양성분표입니다.</small>
        </div>
        <table class="nutrition-table">
          <thead>
            <tr>
              <th>영양소</th>
              <th>100g당 함량</th>
              <th>1포장당 함량</th>
              <th>일일기준치 대비</th>
            </tr>
          </thead>
          <tbody>
  `;

  // 순서대로 표시할 영양소 목록
  const displayOrder = [
    'calories_kcal', 'carbs_g', 'protein_g', 'fat_g', 'saturated_fat_g', 
    'trans_fat_g', 'cholesterol_mg', 'sodium_mg', 'potassium_mg', 
    'fiber_g', 'sugars_g', 'calcium_mg', 'iron_mg', 'phosphorus_mg',
    'vitamin_a_ug', 'thiamine_mg', 'riboflavin_mg', 'niacin_mg', 'vitamin_c_mg'
  ];

  displayOrder.forEach(key => {
    if (fields && fields[key] !== undefined && fields[key] !== null) {
      const value100g = fields[key];
      const valuePackage = fullPackage && fullPackage[key] ? fullPackage[key] : '-';
      const percentage = rdi[key] ? Math.round((value100g / rdi[key]) * 100) : '-';
      
      tableHTML += `
        <tr>
          <td class="nutrient-name">${nutrientNames[key] || key}</td>
          <td class="nutrient-value">${value100g}${units[key] || ''}</td>
          <td class="nutrient-package">${valuePackage !== '-' ? valuePackage + (units[key] || '') : '-'}</td>
          <td class="nutrient-percentage">${percentage !== '-' ? percentage + '%' : '-'}</td>
        </tr>
      `;
    }
  });

  tableHTML += `
          </tbody>
        </table>
        <div class="table-note">
          <small>
            * 일일기준치 대비: 성인 남성(20-49세) 기준 일일권장량 대비 비율<br>
            * 이 정보는 현재 이미지의 개별 제품에 대한 분석 결과입니다<br>
            * 전체 섭취량 분석은 메인 화면의 요약표를 참고하세요
          </small>
        </div>
      </div>
  `;

  // OCR 원시 텍스트 섹션 추가
  if (ocrTexts && ocrTexts.length > 0) {
    tableHTML += `
      <div class="ocr-texts-section">
        <h4>📄 OCR 인식 텍스트</h4>
        <div class="ocr-texts-container">
          <div class="ocr-texts-list">
    `;
    
    ocrTexts.forEach((text, index) => {
      // 숫자와 영양정보 관련 키워드가 포함된 텍스트를 강조
      const isNutritionText = /열량|칼로리|kcal|나트륨|탄수화물|당류|지방|포화지방|트랜스지방|콜레스테롤|단백질|내용량|총량|중량|mg|g/i.test(text);
      const textClass = isNutritionText ? 'ocr-text nutrition-related' : 'ocr-text';
      
      tableHTML += `
        <div class="${textClass}">
          <span class="ocr-index">${index + 1}</span>
          <span class="ocr-content">${text}</span>
        </div>
      `;
    });
    
    tableHTML += `
          </div>
          <div class="ocr-note">
            <small>🟢 녹색 배경: 영양정보 관련 텍스트</small>
          </div>
        </div>
      </div>
    `;
  }

  tableHTML += `
    </div>
  `;

  return tableHTML;
}

// 마크다운 렌더링 공통 함수
function renderMarkdownContent(elementId, markdownText) {
    const element = document.getElementById(elementId);
    if (element && typeof marked !== 'undefined' && markdownText) {
        try {
            // 로딩 메시지 제거
            const loadingElement = element.querySelector('.loading-markdown');
            if (loadingElement) {
                loadingElement.remove();
            }
            
            // 마크다운 파싱 및 렌더링
            element.innerHTML = marked.parse(markdownText);
            console.log(`Markdown rendered for ${elementId}`);
        } catch (error) {
            console.error(`Failed to render markdown for ${elementId}:`, error);
            element.innerHTML = `<p>마크다운 렌더링 중 오류가 발생했습니다.</p><pre>${markdownText}</pre>`;
        }
    }
}

// 페이지 로드 시 마크다운 콘텐츠 초기화
document.addEventListener('DOMContentLoaded', function() {
    // 마크다운 라이브러리 로드 대기
    setTimeout(() => {
        if (typeof marked !== 'undefined') {
            console.log('Marked.js library loaded successfully');
        } else {
            console.warn('Marked.js library not loaded');
        }
    }, 100);
});

