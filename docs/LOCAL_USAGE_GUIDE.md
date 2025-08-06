# 던전톡 MVP - 개인 로컬 사용 가이드

## 📋 목차
1. [시스템 요구사항](#시스템-요구사항)
2. [설치 가이드](#설치-가이드)
3. [환경 설정](#환경-설정)
4. [서버 실행 방법](#서버-실행-방법)
5. [사용 방법](#사용-방법)
6. [문서 관리](#문서-관리)
7. [문제 해결](#문제-해결)
8. [완전 무료 사용법](#완전-무료-사용법)

---

## 🔧 시스템 요구사항

### 최소 요구사항
- **운영체제**: Windows 10/11, macOS, Linux
- **Python**: 3.8 이상 (권장: 3.11+)
- **메모리**: 최소 4GB RAM (권장: 8GB+)
- **저장공간**: 5GB 이상 여유 공간
- **네트워크**: 인터넷 연결 (초기 모델 다운로드용)

### 권장 사양
- **CPU**: 4코어 이상
- **메모리**: 16GB RAM
- **GPU**: CUDA 지원 GPU (선택사항, 성능 향상용)

---

## 🛠 설치 가이드

### 1단계: 프로젝트 클론/다운로드
```bash
# Git이 있는 경우
git clone <repository-url>
cd dungeontalk-mvp

# 또는 ZIP 파일 다운로드 후 압축 해제
```

### 2단계: Python 환경 확인
```bash
python --version
# Python 3.8+ 확인
```

### 3단계: 자동 설치 (Windows)
```cmd
# setup.bat 실행
setup.bat
```

### 3단계: 수동 설치 (모든 OS)
```bash
# UV 패키지 매니저 설치 (10배 빠름)
pip install uv

# 가상환경 생성
uv venv

# 가상환경 활성화
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 의존성 설치
uv pip install -r requirements.txt
```

---

## ⚙️ 환경 설정

### .env 파일 설정

#### 1. Claude API 사용 (유료, 고품질)
```env
# Claude API 설정
ANTHROPIC_API_KEY=your_claude_api_key_here
CLAUDE_MODEL=claude-3-haiku-20240307  # 가장 저렴한 모델

# 모델 선택
LLM_PROVIDER=claude
```

#### 2. Ollama 사용 (완전 무료, 로컬)
```env
# Ollama 설정
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# 모델 선택
LLM_PROVIDER=ollama
```

#### 3. 기본 설정
```env
# FastAPI 설정
API_HOST=0.0.0.0
API_PORT=8005

# 한국어 임베딩 모델
EMBEDDING_MODEL=intfloat/multilingual-e5-large

# 경로 설정
VECTORSTORE_PATH=./vectorstore_new
DOCUMENTS_PATH=./documents
```

---

## 🚀 서버 실행 방법

### 방법 1: 직접 실행
```bash
# 가상환경 활성화
.venv\Scripts\activate    # Windows
source .venv/bin/activate # macOS/Linux

# 서버 시작
python main.py
```

### 방법 2: 백그라운드 실행 (Windows)
```cmd
start /b .venv\Scripts\python.exe main.py
```

### 방법 3: nohup 사용 (macOS/Linux)
```bash
nohup python main.py &
```

### 서버 확인
- 브라우저에서 http://localhost:8005 접속
- API 문서: http://localhost:8005/docs
- 헬스 체크: http://localhost:8005/health

---

## 💬 사용 방법

### 1. 웹 UI 사용 (권장)
```bash
# Streamlit 앱 실행
streamlit run streamlit_app.py
```
- 브라우저에서 http://localhost:8501 자동 열림
- 채팅 인터페이스로 TRPG 게임 진행

### 2. API 직접 사용
```python
import requests

# 채팅 요청
response = requests.post("http://localhost:8005/chat", 
    json={"message": "안녕하세요! 판타지 모험을 시작하고 싶어요"})
print(response.json()["response"])
```

### 3. cURL 사용
```bash
curl -X POST "http://localhost:8005/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "던전 탐험을 시작해주세요"}'
```

---

## 📚 문서 관리

### 지원 파일 형식
- `.txt` - 텍스트 파일
- `.md` - 마크다운 파일  
- `.csv` - CSV 파일

### 문서 추가 방법

#### 1. documents 폴더에 직접 복사
```bash
# 파일을 documents/ 폴더에 복사
cp your_scenario.txt documents/
cp your_npc.md documents/
```

#### 2. API 업로드 사용
```python
import requests

files = {'file': open('your_scenario.txt', 'rb')}
response = requests.post("http://localhost:8005/upload", files=files)
```

#### 3. 자동 스캔
- 서버 시작시 자동으로 documents 폴더 스캔
- 변경된 파일만 자동 임베딩
- 수동 재스캔: `POST /rescan`

### 문서 구조 예시
```
documents/
├── scenarios/
│   ├── 던전_탐험.txt
│   └── 도시_모험.md
├── npcs/
│   ├── 상인_케인.txt
│   └── 마법사_엘리사.txt
├── locations/
│   ├── 신비한_숲.txt
│   └── 버려진_성.md
└── rules/
    ├── 전투_규칙.txt
    └── 마법_시스템.md
```

---

## 🔧 문제 해결

### 일반적인 문제들

#### 1. 서버가 시작되지 않는 경우
```bash
# 의존성 재설치
uv pip install -r requirements.txt --force-reinstall

# 포트 충돌 확인
netstat -ano | findstr :8005  # Windows
lsof -i :8005                 # macOS/Linux
```

#### 2. 모델 다운로드 실패
```bash
# 인터넷 연결 확인
ping huggingface.co

# 캐시 클리어
rm -rf ~/.cache/huggingface/  # macOS/Linux
rmdir /s %USERPROFILE%\.cache\huggingface  # Windows
```

#### 3. 메모리 부족 오류
```env
# .env 파일에서 더 작은 모델 사용
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

#### 4. Claude API 오류
```bash
# API 키 확인
echo $ANTHROPIC_API_KEY  # macOS/Linux
echo %ANTHROPIC_API_KEY% # Windows

# 사용량 확인 (Anthropic 콘솔)
```

### 로그 확인
```bash
# 서버 로그 보기
python main.py 2>&1 | tee server.log

# 오류 디버깅
python -c "import langchain; print('LangChain OK')"
python -c "import chromadb; print('ChromaDB OK')"
```

---

## 💰 완전 무료 사용법

Claude API 없이 완전 무료로 사용하는 방법:

### 1. Ollama 설치
```bash
# Ollama 설치 (https://ollama.ai)
# Windows: ollama-windows-amd64.exe 다운로드
# macOS: brew install ollama
# Linux: curl -fsSL https://ollama.ai/install.sh | sh
```

### 2. 한국어 모델 다운로드
```bash
# 한국어 특화 모델들
ollama pull llama3.2          # 3B 모델 (빠름)
ollama pull llama3.1:8b       # 8B 모델 (균형)
ollama pull qwen2.5:7b        # 중국어+한국어 강함
ollama pull eeve-korean-10.8b # 한국어 특화
```

### 3. .env 설정
```env
# Ollama 무료 사용
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=eeve-korean-10.8b  # 한국어 최적화

# 임베딩도 더 가벼운 모델로
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

### 4. 서버 시작
```bash
# Ollama 서버 시작
ollama serve

# 던전톡 서버 시작 (다른 터미널에서)
python main.py
```

### 무료 사용시 장단점
**장점:**
- ✅ 완전 무료
- ✅ 인터넷 없이 사용 가능
- ✅ 데이터 프라이버시 보장
- ✅ 사용량 제한 없음

**단점:**
- ❌ 응답 품질이 Claude보다 낮음
- ❌ 더 많은 컴퓨터 자원 필요
- ❌ 초기 모델 다운로드 시간 소요

---

## 🎮 게임 시작하기

### 1. 웹 UI에서 게임 시작
```
1. http://localhost:8501 접속
2. "안녕하세요! 판타지 어드벤처를 시작하고 싶어요" 입력
3. GM이 시나리오 제안
4. 선택지를 골라 게임 진행
```

### 2. 게임 예시 대화
```
플레이어: "마법사 캐릭터로 던전 탐험을 시작하고 싶어요"
GM: "당신은 고대 마법사입니다. 어둠에 잠긴 던전 입구 앞에 서 있습니다..."

플레이어: "던전 안으로 들어갑니다"
GM: "횃불의 불빛이 돌계단을 비춥니다. 두 갈래 길이 보입니다..."
```

### 3. 고급 기능 활용
- 📁 **커스텀 시나리오**: documents/ 폴더에 시나리오 파일 추가
- 🤖 **NPC 대화**: 다양한 NPC 파일로 풍부한 상호작용
- 🗺️ **위치 정보**: 상세한 지역 설명 파일 활용
- ⚔️ **전투 시스템**: 규칙 파일 기반 전투 진행

---

## 📞 지원 및 커뮤니티

- **GitHub Issues**: 버그 리포트 및 기능 요청
- **문서 기여**: documents/ 폴더에 새로운 콘텐츠 추가
- **모델 실험**: 다양한 LLM 모델 테스트

즐거운 TRPG 게임 되세요! 🎲✨