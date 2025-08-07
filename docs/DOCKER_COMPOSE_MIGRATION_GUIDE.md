# 🚀 Docker Compose PostgreSQL pgvector 통합 가이드

## 📋 개요

기존 Docker Compose 환경을 던전톡 RAG 시스템의 PostgreSQL + pgvector 구성으로 통합하는 가이드입니다.

## 🔄 현재 상황 vs 목표

### 현재 Docker Compose 구성
```yaml
services:
  postgres:
    image: postgres:17-alpine          # ❌ pgvector 확장 없음
    ports:
      - "5432:5432"                   # ✅ 표준 포트 사용
    environment:
      POSTGRES_DB: dungeondb          # ✅ 동일한 DB 이름
  
  mongo: ...                          # 🤔 RAG 시스템에는 불필요
  valkey-session: ...                 # 🤔 PostgreSQL 세션으로 대체 가능
  valkey-cache: ...                   # ✅ 캐싱용으로 유지 추천
```

### 목표 구성 (RAG 시스템 통합)
```yaml
services:
  postgres:
    image: pgvector/pgvector:pg17     # ✅ pgvector 지원
    ports:
      - "5432:5432"                   # ✅ 표준 포트
    environment:
      POSTGRES_DB: rag_db             # ✅ RAG 전용 DB
```

## 🛠️ 변경 가이드

### 1단계: Docker Compose 파일 수정

#### Option A: 최소 변경 (기존 서비스 유지)
```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16     # 🔄 변경
    container_name: dgt-postgres-rag
    ports:
      - "5433:5432"                   # 🔄 변경
    environment:
      TZ: Asia/Seoul
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: rag_db             # 🔄 변경
    volumes:
      - ./postgres/data:/var/lib/postgresql/data
      - ./postgres/init.sql:/docker-entrypoint-initdb.d/init.sql  # 🆕 추가

  mongo:
    # 기존 설정 유지
    image: mongo:7.0
    ports:
      - "27017:27017"
    # ... (나머지 동일)

  valkey-session:
    # ⚠️ 선택: PostgreSQL 세션 사용시 제거 가능
    # 기존 설정 유지하거나 제거

  valkey-cache:
    # ✅ 캐싱용으로 유지 권장
    image: valkey/valkey:latest
    container_name: dgt-valkey-cache
    # ... (기존 설정 유지)
```

#### Option B: RAG 전용 최적화 (권장)
```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: dgt-postgres-rag
    ports:
      - "5432:5432"
    environment:
      TZ: Asia/Seoul
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: dungeondb
    volumes:
      - ./postgres/data:/var/lib/postgresql/data
      - ./postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped

  valkey-cache:
    image: valkey/valkey:latest
    container_name: dgt-valkey-cache
    ports:
      - "${VALKEY_CACHE_PORT}:6379"
    environment:
      TZ: Asia/Seoul
    volumes:
      - ./valkey-cache/data:/data
      - "${VALKEY_CACHE_CONFIG_PATH}:/etc/valkey/valkey.conf"
    command: ["valkey-server", "/etc/valkey/valkey.conf"]
    restart: unless-stopped

  # mongo, valkey-session 제거
```

### 2단계: 초기화 스크립트 생성

**파일 생성**: `./postgres/init.sql`

```sql
-- 🔧 pgvector 확장 활성화
CREATE EXTENSION IF NOT EXISTS vector;

-- 📊 세션 관리 테이블 생성
CREATE TABLE IF NOT EXISTS chat_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    user_name VARCHAR(255) NOT NULL,  
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 🚀 성능 최적화 인덱스
CREATE INDEX IF NOT EXISTS idx_chat_sessions_session_id 
ON chat_sessions(session_id);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at 
ON chat_sessions(created_at);

-- 📝 초기화 완료 로그
INSERT INTO chat_sessions (session_id, user_name, message, response) 
VALUES ('system', 'admin', 'Database initialized', 'pgvector RAG system ready')
ON CONFLICT DO NOTHING;
```

### 3단계: 환경변수 설정

**`.env` 파일 업데이트**:

```bash
# 🗄️ PostgreSQL 설정 (기존과 통합)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DB=rag_db

# 🤖 RAG 시스템 설정
USE_POSTGRESQL=true
USE_REMOTE_EMBEDDINGS=true

# 🧠 AI API 설정
OPENAI_API_KEY=sk-proj-your-openai-key-here
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

DEEPSEEK_API_KEY=sk-your-deepseek-key-here
DEEPSEEK_MODEL=deepseek-chat

LLM_PROVIDER=deepseek

# ⚡ Valkey 캐시 설정 (유지시)
VALKEY_CACHE_PORT=6380
VALKEY_CACHE_CONFIG_PATH=./valkey-cache/valkey.conf

# 🗂️ 문서 및 벡터스토어 설정
DOCUMENTS_PATH=./documents
VECTORSTORE_PATH=./vectorstore

# 📊 성능 튜닝
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
SEARCH_K=3
RECENT_CHAT_COUNT=5
MAX_SESSIONS=100
```

### 4단계: 디렉토리 구조 생성

```bash
# 📁 필요한 디렉토리 생성
mkdir -p postgres/data
mkdir -p postgres
mkdir -p valkey-cache/data
mkdir -p documents

# 📝 초기화 스크립트 생성 (위의 init.sql 내용으로)
touch postgres/init.sql
```

## 🚦 마이그레이션 단계

### Phase 1: 기존 데이터 백업 (중요!)
```bash
# 기존 PostgreSQL 데이터 백업
docker exec your-current-postgres pg_dump -U postgres dungeondb > backup.sql
```

### Phase 2: 새 컨테이너 시작
```bash
# 기존 컨테이너 중지
docker-compose down

# 새 구성으로 시작
docker-compose up -d postgres

# 로그 확인
docker-compose logs postgres
```

### Phase 3: pgvector 확인
```bash
# pgvector 확장 확인
docker exec -it postgres-pgvector psql -U root -d dungeondb -c "SELECT * FROM pg_extension WHERE extname='vector';"

# 테이블 생성 확인
docker exec -it postgres-pgvector psql -U root -d dungeondb -c "\dt"
```

### Phase 4: RAG 시스템 테스트
```bash
# Python 서버 시작 (uv 환경)
uv run python main.py

# 헬스체크
curl http://localhost:8000/health

# 문서 스캔 확인
curl -X POST http://localhost:8000/rescan
```

## 📊 성능 및 리소스

### 메모리 사용량 비교
```
┌─────────────────┬──────────────┬──────────────┐
│ 구성            │ 기존         │ 새 구성      │
├─────────────────┼──────────────┼──────────────┤
│ PostgreSQL      │ ~100MB       │ ~150MB       │
│ MongoDB         │ ~100MB       │ 제거(-100MB) │
│ Valkey Session  │ ~50MB        │ 제거(-50MB)  │
│ Valkey Cache    │ ~50MB        │ ~50MB        │
│ Python RAG      │ 없음         │ +900MB       │
├─────────────────┼──────────────┼──────────────┤
│ 총합            │ ~300MB       │ ~1.1GB       │
└─────────────────┴──────────────┴──────────────┘
```

### 디스크 사용량
```
- PostgreSQL 데이터: ~650KB (벡터 58개)
- 문서 파일: ~2MB (TRPG 문서 23개)
- 컨테이너 이미지: +200MB (pgvector)
```

## 🔧 트러블슈팅

### 포트 충돌 문제
```bash
# 포트 5433 사용 중인 프로세스 확인
netstat -tulpn | grep 5433

# 기존 PostgreSQL 컨테이너 중지
docker stop postgres-rag
```

### pgvector 확장 오류
```sql
-- 수동으로 확장 생성
CREATE EXTENSION IF NOT EXISTS vector;

-- 확장 확인
\dx
```

### 연결 문제
```bash
# 컨테이너 로그 확인
docker-compose logs postgres

# 네트워크 연결 테스트
telnet localhost 5433
```

## 📈 운영 최적화

### Docker Compose 추가 설정
```yaml
services:
  postgres:
    # ... 기존 설정
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```

### 백업 자동화
```bash
# crontab에 추가
0 2 * * * docker exec dgt-postgres-rag pg_dump -U postgres rag_db > /backup/rag_db_$(date +\%Y\%m\%d).sql
```

## ✅ 최종 체크리스트

- [ ] Docker Compose 파일 수정
- [ ] `postgres/init.sql` 파일 생성
- [ ] `.env` 파일 환경변수 추가
- [ ] 기존 데이터 백업 (필요시)
- [ ] 새 컨테이너 시작 및 테스트
- [ ] pgvector 확장 확인
- [ ] RAG 시스템 동작 확인
- [ ] 성능 모니터링 설정

## 🎯 결과

성공적으로 통합하면 다음을 얻게 됩니다:

✅ **완전한 PostgreSQL + pgvector RAG 시스템**
✅ **영구적인 세션 및 벡터 데이터 저장**  
✅ **기존 Docker 환경과의 호환성**
✅ **확장 가능한 아키텍처**

---

📝 **작성일**: 2025-08-06  
🔄 **버전**: 1.0  
👨‍💻 **작성자**: Claude Code Assistant