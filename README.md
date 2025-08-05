# 🎲 던전톡 RAG MVP - Dev Branch

TRPG(테이블탑 RPG) AI 어시스턴트 - RAG 기반 던전마스터

> **리팩토링 완료!** 멀티유저 세션 지원, Spring Boot 연동 준비, 성능 최적화가 포함된 개발 브랜치입니다.

## 🚀 Dev Branch 주요 변경사항

### ✨ 새로운 기능
- **멀티유저 세션 관리**: 3명이 같은 방에서 함께 TRPG 플레이 가능
- **Spring Boot 완벽 연동**: 상세한 연동 가이드와 예제 코드 제공
- **세션별 대화 분리**: 각 방마다 독립된 AI 던전마스터
- **화자 구분 시스템**: 누가 말했는지 정확히 기록

### 🔧 기술적 개선
- **SessionManager 클래스**: 전역 변수 → 클래스 기반 관리로 리팩토링
- **환경변수 설정**: 하드코딩된 값들을 .env로 이동하여 설정 가능
- **LangChain 최신화**: deprecated 메서드 → invoke() 방식으로 업데이트
- **향상된 에러 처리**: 구체적인 예외 타입별 처리 및 로깅 개선

### 📚 문서화
- **SPRING_BOOT_INTEGRATION.md**: 완전한 Spring Boot 연동 가이드
- **SPRING_INTEGRATION_GUIDE.md**: 기존 간단 가이드 (호환성 유지)

---

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
- **FastAPI**: REST API 서버 (포트 8000)
- **Streamlit**: 웹 UI (개발/테스트용)
- **Spring Boot**: 백엔드 연동 준비 완료
- **Claude 3.5 Sonnet / DeepSeek / Ollama**: 다중 LLM 지원
- **ChromaDB**: 벡터 데이터베이스
- **LangChain**: RAG 파이프라인 (최신 버전 호환)

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

---

## 🌱 Spring Boot 연동

본 브랜치는 Spring Boot와의 완벽한 연동을 지원합니다.

### 📖 연동 가이드
- **[SPRING_BOOT_INTEGRATION.md](./SPRING_BOOT_INTEGRATION.md)**: 완전한 연동 가이드
  - 단계별 구현 방법
  - 실제 동작하는 예제 코드
  - 에러 처리 및 최적화
  - 프론트엔드 연동 방법

### 🎯 주요 API 엔드포인트
```bash
# 멀티유저 채팅 (Spring Boot에서 호출)
POST /chat
{
  "session_id": "room_abc123",
  "user_name": "김철수", 
  "message": "안녕하세요"
}

# 세션 목록 조회
GET /sessions

# 세션별 대화 기록
GET /sessions/{session_id}/history
```

### 🚀 빠른 시작 (Spring Boot 개발자용)
1. Python 서버 실행: `python main.py` (포트 8000)
2. Spring Boot에서 WebClient로 `/chat` 엔드포인트 호출
3. 세션 ID와 사용자명을 포함하여 요청
4. AI 응답 받아서 프론트엔드에 전달

자세한 내용은 [SPRING_BOOT_INTEGRATION.md](./SPRING_BOOT_INTEGRATION.md)를 참고하세요.