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
    
    // 파일 업로드 진행 상황부터 시작
    simulateFileUploadProgress(files, () => {
      // 업로드 완료 후 실제 처리 과정 시뮬레이션 시작
      simulateRealisticProgress(files);
    });
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

// 결과 화면을 애니메이션과 함께 표시
function showResultsWithAnimation() {
  // 페이지 새로고침 대신 결과 영역으로 스크롤
  const resultsSection = document.querySelector('.results');
  if (resultsSection) {
    // 결과 섹션이 이미 있는 경우 스크롤
    resultsSection.style.opacity = '0';
    resultsSection.style.transform = 'translateY(20px)';
    resultsSection.style.transition = 'opacity 0.8s ease-out, transform 0.8s ease-out';
    
    setTimeout(() => {
      resultsSection.style.opacity = '1';
      resultsSection.style.transform = 'translateY(0)';
      
      // 부드러운 스크롤
      resultsSection.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'start' 
      });
    }, 100);
  } else {
    // 결과가 없는 경우 페이지 새로고침 (폴백)
    console.log('No results section found, reloading page...');
    setTimeout(() => {
      window.location.reload();
    }, 1000);
  }
}

// LLM 스트리밍 응답 처리
function updateLLMResponse(data) {
  const { type, data: content, full_response } = data;
  
  if (type === 'chunk') {
    // 실시간으로 텍스트 추가
    updateRecommendationText(content, false);
  } else if (type === 'complete') {
    // 완료된 응답 표시
    updateRecommendationText(full_response || content, true);
    updateAnalysisStep('step-complete', 100, '모든 분석이 완료되었습니다!');
    
    // 매끄러운 화면 전환
    handleAnalysisComplete();
  } else if (type === 'error') {
    console.error('LLM Error:', content);
    updateRecommendationText(content, true);
  }
}

// 추천 텍스트 업데이트
function updateRecommendationText(content, isComplete) {
  const maleRecommendationElement = document.querySelector('#male-recommendation .recommendation-content-text');
  const femaleRecommendationElement = document.querySelector('#female-recommendation .recommendation-content-text');
  
  if (maleRecommendationElement) {
    if (isComplete) {
      maleRecommendationElement.innerHTML = content.replace(/\n/g, '<br>');
    } else {
      maleRecommendationElement.innerHTML += content.replace(/\n/g, '<br>');
    }
  }
  
  if (femaleRecommendationElement) {
    if (isComplete) {
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
  thumbnailContainers.forEach((container, index) => {
    container.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      
      // onclick 속성에서 파라미터 추출
      const onclickAttr = container.getAttribute('onclick');
      if (onclickAttr) {
        console.log('Executing onclick:', onclickAttr);
        try {
          // onclick 속성 실행
          eval(onclickAttr);
        } catch (error) {
          console.error('Error executing onclick:', error);
        }
      } else {
        console.log('No onclick attribute found on thumbnail container');
      }
    });
  });
}

// 이미지 상세보기 (전역 함수)
function showImageDetail(filename, status, imageUrl, fields, fullPackage) {
  console.log('showImageDetail called with:', { filename, status, imageUrl, fields, fullPackage });
  
  // 기존 모달이 있으면 제거
  const existingModal = document.querySelector('.image-detail-modal');
  if (existingModal) {
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
          <h3>이미지 상세 정보</h3>
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
              generateNutritionTable(fields, fullPackage)
            }
          </div>
        </div>
      </div>
    </div>
  `;
  
  document.body.appendChild(modal);
  
  // 애니메이션을 위해 다음 프레임에 show 클래스 추가
  requestAnimationFrame(() => {
    modal.classList.add('show');
  });
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
        
        // 파일 업로드 진행 상황부터 시작
        simulateFileUploadProgress(files, () => {
          // Socket.IO를 통한 실시간 분석 시작
          if (socket && isSocketConnected) {
            const filesData = files.map(file => ({
              name: file.name,
              size: file.size,
              type: file.type
            }));
            
            console.log('Starting real-time analysis via Socket.IO');
            socket.emit('start_analysis', { files: filesData });
          } else {
            // 대체: 기존 시뮬레이션 사용
            console.log('Socket.IO not available, using simulation');
            simulateRealisticProgress(files);
          }
        });
      }
      
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
function generateNutritionTable(fields, fullPackage) {
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
        <h4>분석된 영양정보</h4>
        <table class="nutrition-table">
          <thead>
            <tr>
              <th>영양소</th>
              <th>100g당</th>
              <th>전체 패키지</th>
              <th>% 영양성분기준치</th>
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
          <small>* % 영양성분기준치: 성인 남성 일일권장량 대비 비율</small>
        </div>
      </div>
    </div>
  `;

  return tableHTML;
}

