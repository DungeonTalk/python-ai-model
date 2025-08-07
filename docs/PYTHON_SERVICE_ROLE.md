# Python AI Service 역할 및 아키텍처 가이드

## 🎯 서비스 개요

Python FastAPI는 던전톡 프로젝트에서 **순수 AI 응답 생성 서비스**로 역할을 담당합니다. 마이크로서비스 아키텍처의 일부로서 AI 관련 기능만을 전담합니다.

## 🏗️ 전체 아키텍처

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   프론트엔드     │◄──►│   Spring Boot    │◄──►│  Python FastAPI │
│   (React/Vue)   │    │   (게임 서버)     │    │   (AI 서버)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                           │
                              ▼                           ▼
                       ┌──────────────┐           ┌──────────────┐
                       │   게임 DB    │           │ Vector DB    │
                       │ (PostgreSQL) │           │(PostgreSQL) │
                       └──────────────┘           └──────────────┘
```

## 🐍 Python FastAPI의 역할

### ✅ **담당하는 것들**

#### 1. **RAG (검색 증강 생성) 엔진**
- 문서 임베딩 및 벡터 검색
- 관련 문서 컨텍스트 추출
- PostgreSQL + pgvector를 통한 벡터 저장

#### 2. **AI 응답 생성**
- LLM을 통한 GM 답변 생성
- 다양한 AI 모델 지원 (Claude, DeepSeek, OpenAI)
- TRPG에 특화된 프롬프트 엔지니어링

#### 3. **문서 관리**
- TRPG 관련 문서 자동 임베딩
- 파일 변경 감지 및 재처리
- 다양한 파일 포맷 지원 (.txt, .md, .csv)

### ❌ **담당하지 않는 것들**

#### 1. **세션 관리** → Spring Boot로 이관
- 사용자 세션 추적
- 대화 기록 저장/조회
- 플레이어 상태 관리

#### 2. **실시간 통신** → Spring Boot에서 구현
- WebSocket 연결
- 실시간 채팅
- 플레이어 동기화

#### 3. **게임 로직** → Spring Boot에서 구현
- 방 생성/관리
- 플레이어 입장/퇴장
- 게임 상태 관리

## 🔧 현재 구현 상태

### **주요 컴포넌트**

#### 1. **RAGEngine 클래스**
```python
class RAGEngine:
    def __init__(self):
        # 임베딩 모델 초기화
        # PostgreSQL PGVector 연결
        # LLM 모델 설정
    
    def query(self, question: str, session_history: list, current_user: str):
        # 벡터 검색 + AI 응답 생성
```

#### 2. **PostgreSQLSessionManager 클래스** (제거 예정)
- 현재는 세션 관리를 하고 있지만, Spring Boot로 이관 예정
- 마이크로서비스 분리를 위해 제거할 예정

#### 3. **API 엔드포인트**
- `POST /chat` - 현재 복합 기능 (간소화 예정)
- `GET /health` - 헬스체크


## 🚀 개선 계획

### **1단계: API 간소화**
```python
# 기존 복잡한 엔드포인트
@app.post("/chat")
async def chat(request: ChatRequest):
    # 세션 관리 + AI 응답 (너무 많은 책임)

# 목표: 간단한 엔드포인트
@app.post("/generate")
async def generate_response(request: SimpleRequest):
    # 순수 AI 응답만 생성
```

### **2단계: 세션 관리 제거**
- `PostgreSQLSessionManager` 클래스 삭제
- 세션 관련 모든 엔드포인트 제거
- 데이터베이스 의존성 최소화

### **3단계: 순수 AI 서비스화**
```python
class SimpleRequest(BaseModel):
    question: str
    context: str  # Spring Boot에서 제공하는 대화 기록
    user_name: str

class SimpleResponse(BaseModel):
    answer: str
    sources: list[str]
```

## 📊 Spring Boot와의 연동 방식

### **호출 흐름**
1. **사용자** → Spring Boot에 메시지 전송
2. **Spring Boot** → 자체 DB에서 대화 기록 조회
3. **Spring Boot** → Python API 호출 (`/generate`)
4. **Python** → AI 답변 생성 후 반환
5. **Spring Boot** → 답변을 DB에 저장
6. **Spring Boot** → 실시간으로 모든 플레이어에게 전송

### **데이터 흐름**
```json
// Spring Boot → Python 요청
{
  "question": "던전에 들어갑니다",
  "context": "이전 대화 기록...",
  "user_name": "플레이어1"
}

// Python → Spring Boot 응답
{
  "answer": "어둠 속에서 차가운 바람이...",
  "sources": ["던전_입구_설명.txt", "몬스터_정보.txt"]
}
```

## 🔒 보안 및 성능 고려사항

### **보안**
- API 키 환경변수 관리
- Spring Boot와의 내부 통신 보안
- 입력 검증 및 sanitization

### **성능**
- 벡터 검색 캐싱
- 모델 로딩 최적화  
- 비동기 처리
- 응답 시간 모니터링

## 📈 모니터링 및 로깅

### **주요 메트릭**
- AI 응답 생성 시간
- 벡터 검색 성능
- API 호출 빈도
- 에러 발생률

### **로깅**
- 구조화된 JSON 로그
- 요청/응답 추적
- 성능 병목 지점 식별

## 🛠️ 개발 환경

### **기술 스택**
- **Framework**: FastAPI
- **AI/ML**: LangChain, OpenAI, Anthropic, DeepSeek
- **Vector DB**: PostgreSQL + pgvector
- **Package Manager**: uv
- **Python Version**: 3.13+

### **의존성**
- `fastapi`: 웹 프레임워크
- `langchain-*`: LLM 통합
- `psycopg[binary]`: PostgreSQL 연결
- `uvicorn`: ASGI 서버

## 🎮 TRPG 특화 기능

### **프롬프트 엔지니어링**
- GM 역할에 최적화된 프롬프트
- 상황별 적응형 응답 생성
- 다중 플레이어 고려한 답변

### **게임 요소 지원**
- 주사위 굴리기 명령어 파싱 (예정)
- NPC 대화 모드 (예정)
- 상황별 분위기 연출 (예정)

---

## 📝 버전 히스토리

- **v0.1.0**: 기본 RAG 엔진 구현
- **v0.2.0**: PostgreSQL 연동 및 세션 관리
- **v0.3.0**: 다중 LLM 지원
- **v0.4.0**: ChromaDB 제거, PostgreSQL 전용 최적화
- **v1.0.0 (예정)**: Spring Boot 연동을 위한 API 간소화

---

*이 문서는 던전톡 프로젝트의 Python AI 서비스 아키텍처를 설명합니다. 궁금한 점이나 개선 제안이 있으시면 개발팀에 문의해 주세요.*