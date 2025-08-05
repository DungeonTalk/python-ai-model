# 🎲 던전톡 RAG MVP

TRPG(테이블탑 RPG) AI 어시스턴트 - RAG 기반 던전마스터

> **완전 초보자도 5분만에 설치 가능!** Claude AI가 당신의 TRPG 문서를 학습하여 지능적인 던전마스터가 됩니다.

## 📋 사전 준비물

### 1. Python 설치 (필수)
- **Python 3.8 이상** 필요
- [python.org](https://www.python.org/downloads/)에서 다운로드
- 설치시 **"Add Python to PATH"** 체크 필수!

### 2. Claude API 키 발급 (필수)
1. [Claude Console](https://console.anthropic.com) 접속
2. 회원가입/로그인
3. **"Create Key"** 클릭
4. API 키 복사 (sk-ant-api03-로 시작)
5. **💳 크레딧 충전** (약 $5 권장)

### 3. Git 설치 (선택사항)
- [git-scm.com](https://git-scm.com/)에서 다운로드
- 또는 GitHub Desktop 사용

## 🚀 5분 설치 가이드

### 1단계: 저장소 다운로드

**방법 A: Git 사용**
```bash
git clone https://github.com/DungeonTalk/python-ai-model.git
cd python-ai-model
```

**방법 B: ZIP 다운로드**
1. [GitHub 페이지](https://github.com/DungeonTalk/python-ai-model)에서 **"Code" → "Download ZIP"**
2. 압축 해제 후 폴더로 이동

### 2단계: 자동 설치 (Windows)
```bash
setup.bat
```
> ⚡ **UV 고속 설치**: 기존 pip보다 10배 빠른 설치 (약 15초)

**Mac/Linux 사용자:**
```bash
pip install uv
uv venv
uv pip install -r requirements.txt
```

### 3단계: Claude API 키 설정
1. `.env.example` 파일을 `.env`로 복사
2. 메모장으로 `.env` 파일 열기
3. 다음과 같이 수정:
```env
ANTHROPIC_API_KEY=sk-ant-api03-여기에_발급받은_API_키_붙여넣기
```
4. 저장

### 4단계: 실행
**터미널 1 (FastAPI 서버):**
```bash
python main.py
```

**터미널 2 (웹 UI):**
```bash
streamlit run streamlit_app.py
```

## 🌐 접속 주소
- **🎯 웹 채팅**: http://localhost:8501 (메인 사용)
- **📚 API 문서**: http://localhost:8005/docs (개발자용)

## 📚 사용법

### 1. TRPG 문서 추가하기

**방법 A: 폴더에 직접 추가**
1. `documents/` 폴더 열기
2. TRPG 문서 파일 복사 (`.txt`, `.md`, `.csv` 지원)
3. 서버 재시작 → 자동 임베딩

**방법 B: 웹에서 업로드**
1. http://localhost:8501 접속
2. 왼쪽 사이드바 "문서 업로드" 섹션
3. 파일 선택 후 "업로드" 버튼

**추천 문서 종류:**
```
📁 documents/
├── NPC_캐릭터명.txt          # NPC 설정
├── 아이템_무기류.txt          # 아이템 정보  
├── 세계관_배경설정.txt        # 세계관 설명
├── 시나리오_첫번째모험.txt    # 시나리오
├── 규칙_전투시스템.txt        # 룰북
└── 퀘스트_메인스토리.txt      # 퀘스트
```

### 2. AI 던전마스터와 대화하기

**질문 예시:**
- **아이템**: "근접무기 중에 좋은 게 뭐 있어?"
- **NPC**: "엘프 현자가 누구야? 어떤 사람이야?"
- **세계관**: "황혼의 새벽 세계관에 대해 설명해줘"
- **전투**: "오크 3마리와 싸우게 되면 어떻게 해야 해?"
- **스토리**: "플레이어가 마을에 도착했어, 무슨 일이 일어날까?"

### 3. 고급 사용법

**문서 재스캔:**
- 문서 추가 후 서버 재시작 없이 반영하기
```bash
curl -X POST "http://localhost:8005/rescan"
```

**API 직접 사용:**
```bash
curl -X POST "http://localhost:8005/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "근접무기 추천해줘"}'
```

## 🛠 기술 스택
- **FastAPI**: REST API 서버
- **Streamlit**: 웹 UI
- **Claude 3.5 Sonnet**: LLM
- **ChromaDB**: 벡터 데이터베이스
- **LangChain**: RAG 파이프라인

## 📋 요구사항
- Python 3.8+
- Claude API 키 (https://console.anthropic.com)
- 메모리 4GB+ 권장

## 🔧 문제 해결

### ❌ Python 관련 오류

**"python이 인식되지 않습니다"**
```bash
# 해결: Python PATH 설정
1. Python 재설치 (Add to PATH 체크)
2. 또는 명령어: py main.py
```

**"ModuleNotFoundError" 오류**
```bash
# 해결 1: UV 재설치 (권장)
setup.bat

# 해결 2: 수동 설치
uv pip install -r requirements.txt

# 해결 3: pip 사용
pip install -r requirements.txt
```

### ❌ Claude API 관련 오류

**"Invalid API key" 오류**
1. `.env` 파일에서 API 키 확인
2. `sk-ant-api03-`로 시작하는지 확인
3. [Claude Console](https://console.anthropic.com)에서 키 재생성

**"Insufficient credits" 오류**
- Claude Console에서 크레딧 충전 ($5 권장)

**응답이 영어로 나오는 경우**
- 서버 재시작 (python main.py)
- documents 폴더에 한국어 문서 추가

### ❌ 서버 접속 오류

**"Failed to connect to localhost" 오류**
```bash
# 서버 상태 확인
netstat -ano | findstr :8005

# 서버 재시작
python main.py
```

**Streamlit 웹페이지가 안 열리는 경우**
```bash
# 포트 변경해서 실행
streamlit run streamlit_app.py --server.port 8502
```

### ❌ 문서/임베딩 관련

**업로드한 문서가 반영 안 되는 경우**
1. 서버 재시작 (자동 임베딩)
2. 또는 재스캔 API 호출:
```bash
curl -X POST "http://localhost:8005/rescan"
```

**AI가 문서 내용을 모르는 경우**
- 파일 확장자 확인 (`.txt`, `.md`, `.csv`만 지원)
- 파일 인코딩이 UTF-8인지 확인
- 문서가 `documents/` 폴더에 있는지 확인

### ❌ 성능 관련

**응답이 너무 느린 경우**
- Claude API 서버 상태 확인
- 인터넷 연결 확인
- 문서 수가 너무 많은 경우 일부 제거

**메모리 부족 오류**
- 컴퓨터 재시작
- 다른 프로그램 종료
- RAM 4GB 이상 권장

### 🆘 여전히 안 되는 경우

**로그 확인:**
```bash
python main.py
# 에러 메시지 복사해서 GitHub Issues에 문의
```

**GitHub Issues에 문의:**
- [이슈 등록](https://github.com/DungeonTalk/python-ai-model/issues)
- 에러 메시지와 실행 환경 포함