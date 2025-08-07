# 🐳 Docker PostgreSQL pgvector 구성 가이드

## 📋 개요

던전톡 RAG 시스템에서 사용하는 Docker PostgreSQL + pgvector 환경 구성에 대한 완전한 가이드입니다.

## 🏗️ 현재 Docker 구성

### 사용 중인 컨테이너
```yaml
Container Name: postgres-pgvector
Image: pgvector/pgvector:pg17
Port Mapping: 5432:5432
Database: dungeondb
Status: ✅ 실행 중
```

## 🚀 Docker 실행 가이드

### 1단계: pgvector PostgreSQL 컨테이너 실행

```bash
# pgvector 지원 PostgreSQL 17 컨테이너 실행
docker run -d \
  --name postgres-pgvector \
  -p 5432:5432 \
  -e POSTGRES_USER=root \
  -e POSTGRES_PASSWORD=1234 \
  -e POSTGRES_DB=dungeondb \
  -v $(pwd)/postgres-data:/var/lib/postgresql/data \
  pgvector/pgvector:pg17
```

### 2단계: pgvector 확장 활성화

```bash
# 컨테이너에 접속
docker exec -it postgres-pgvector psql -U root -d dungeondb

# pgvector 확장 생성
CREATE EXTENSION IF NOT EXISTS vector;

# 확장 확인
\dx

# 종료
\q
```

### 3단계: 세션 테이블 생성

```bash
# 세션 관리용 테이블 생성
docker exec -it postgres-rag psql -U postgres -d rag_db -c "
CREATE TABLE IF NOT EXISTS chat_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    user_name VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_session_id ON chat_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at ON chat_sessions(created_at);
"
```

## 🔧 Docker Compose 버전

### docker-compose.yml 예시

```yaml
version: '3.8'

services:
  postgres-rag:
    image: pgvector/pgvector:pg16
    container_name: postgres-rag
    ports:
      - "5433:5432"
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=rag_db
      - POSTGRES_INITDB_ARGS=--encoding=UTF-8
    volumes:
      - ./postgres-data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d rag_db"]
      interval: 30s
      timeout: 10s
      retries: 3

  # 선택사항: Redis 캐시 (성능 향상)
  redis-cache:
    image: redis:7-alpine
    container_name: rag-redis
    ports:
      - "6379:6379"
    restart: unless-stopped
```

### 초기화 스크립트 (선택사항)

**파일**: `./init-scripts/01-init.sql`

```sql
-- pgvector 확장 생성
CREATE EXTENSION IF NOT EXISTS vector;

-- 세션 관리 테이블
CREATE TABLE IF NOT EXISTS chat_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    user_name VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_chat_sessions_session_id ON chat_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at ON chat_sessions(created_at);

-- 초기 테스트 데이터 (선택사항)
INSERT INTO chat_sessions (session_id, user_name, message, response) 
VALUES ('system', 'admin', 'Database initialized', 'pgvector RAG system ready')
ON CONFLICT DO NOTHING;
```

## 📊 환경별 설정

### 개발 환경
```bash
# 간단한 실행
docker run -d --name postgres-pgvector \
  -p 5432:5432 \
  -e POSTGRES_USER=root \
  -e POSTGRES_PASSWORD=1234 \
  -e POSTGRES_DB=dungeondb \
  pgvector/pgvector:pg17
```

### 운영 환경
```bash
# 영구 볼륨과 보안 설정
docker run -d --name postgres-pgvector \
  -p 5433:5432 \
  -e POSTGRES_USER=rag_user \
  -e POSTGRES_PASSWORD=${SECURE_PASSWORD} \
  -e POSTGRES_DB=rag_db \
  -v /opt/postgres-data:/var/lib/postgresql/data \
  --restart=always \
  --memory=1g \
  --cpus=1 \
  pgvector/pgvector:pg16
```

## 🔍 확인 및 테스트

### 컨테이너 상태 확인
```bash
# 실행 중인 컨테이너 확인
docker ps | grep postgres-rag

# 컨테이너 로그 확인
docker logs postgres-rag

# 리소스 사용량 확인
docker stats postgres-rag
```

### 데이터베이스 연결 테스트
```bash
# PostgreSQL 연결 테스트
docker exec postgres-rag pg_isready -U postgres -d rag_db

# 테이블 확인
docker exec postgres-rag psql -U postgres -d rag_db -c "\dt"

# pgvector 확장 확인
docker exec postgres-rag psql -U postgres -d rag_db -c "SELECT * FROM pg_extension WHERE extname='vector';"
```

### Python 연결 테스트
```python
import psycopg2

# 연결 테스트
try:
    conn = psycopg2.connect(
        host="localhost",
        port=5433,
        database="rag_db",
        user="postgres",
        password="postgres"
    )
    print("✅ PostgreSQL 연결 성공!")
    conn.close()
except Exception as e:
    print(f"❌ 연결 실패: {e}")
```

## 🗂️ 데이터 관리

### 백업 및 복원
```bash
# 데이터베이스 백업
docker exec postgres-pgvector pg_dump -U root dungeondb > dungeondb_backup.sql

# 데이터베이스 복원
docker exec -i postgres-pgvector psql -U root dungeondb < dungeondb_backup.sql

# 볼륨 백업
docker run --rm -v postgres-pgvector_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

### 데이터 초기화
```bash
# 기존 데이터 삭제 후 재시작
docker stop postgres-pgvector
docker rm postgres-pgvector
docker volume rm postgres-pgvector_data  # 주의: 모든 데이터 삭제!

# 새로 시작
uv run python -c "
import psycopg2
conn = psycopg2.connect('postgresql://root:1234@localhost:5432/dungeondb')
cur = conn.cursor()
cur.execute('CREATE SCHEMA IF NOT EXISTS dungeontalk_rag;')
cur.execute('CREATE EXTENSION IF NOT EXISTS vector SCHEMA public;')
conn.commit()
conn.close()
print('프로젝트 초기화 완료')
"
```

## 🚨 트러블슈팅

### 자주 발생하는 문제들

#### 1. 포트 충돌
```bash
# 포트 5433 사용 중 확인
netstat -an | findstr 5433

# 다른 포트 사용
docker run ... -p 5434:5432 ...
```

#### 2. 권한 문제
```bash
# 볼륨 권한 확인
ls -la ./postgres-data/

# 권한 수정 (Linux/macOS)
sudo chown -R 999:999 ./postgres-data/
```

#### 3. 메모리 부족
```bash
# 메모리 제한 설정
docker run ... --memory=512m --memory-swap=1g ...
```

#### 4. pgvector 확장 오류
```sql
-- 수동 설치 (컨테이너 내부)
CREATE EXTENSION IF NOT EXISTS vector;

-- 확인
SELECT name, default_version, installed_version 
FROM pg_available_extensions 
WHERE name = 'vector';
```

## 📈 성능 최적화

### PostgreSQL 설정 튜닝
```sql
-- postgresql.conf 최적화 (컨테이너 내부)
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';

-- 설정 리로드
SELECT pg_reload_conf();
```

### Docker 리소스 제한
```bash
# 적절한 리소스 할당
docker run -d \
  --name postgres-rag \
  --memory=1g \
  --memory-swap=2g \
  --cpus=1 \
  --restart=unless-stopped \
  [... 기타 옵션]
```

## 📊 모니터링

### 기본 모니터링
```bash
# 실시간 통계
docker stats postgres-rag

# 연결 수 확인
docker exec postgres-rag psql -U postgres -d rag_db -c "SELECT count(*) FROM pg_stat_activity;"

# 데이터베이스 크기 확인
docker exec postgres-rag psql -U postgres -d rag_db -c "
SELECT 
    pg_size_pretty(pg_database_size('rag_db')) as database_size,
    pg_size_pretty(pg_total_relation_size('langchain_pg_embedding')) as vector_table_size;
"
```

### 로그 모니터링
```bash
# 실시간 로그 확인
docker logs -f postgres-rag

# 최근 로그 확인
docker logs --tail 100 postgres-rag
```

## 🔧 유지보수

### 정기 작업
```bash
# 1. 데이터베이스 VACUUM (매주)
docker exec postgres-rag psql -U postgres -d rag_db -c "VACUUM ANALYZE;"

# 2. 로그 정리 (매월)
docker logs postgres-rag 2>&1 | tail -1000 > postgres_recent.log

# 3. 백업 (매일)
docker exec postgres-rag pg_dump -U postgres rag_db | gzip > "backup_$(date +%Y%m%d).sql.gz"
```

### 업그레이드
```bash
# 1. 현재 데이터 백업
docker exec postgres-rag pg_dump -U postgres rag_db > pre_upgrade_backup.sql

# 2. 새 버전으로 교체
docker stop postgres-rag
docker pull pgvector/pgvector:pg17  # 새 버전
docker run -d --name postgres-rag-new [... 동일 설정] pgvector/pgvector:pg17

# 3. 데이터 복원 및 테스트
```

## 📋 체크리스트

### 초기 설정
- [ ] pgvector/pgvector:pg16 이미지 다운로드
- [ ] 컨테이너 실행 (포트 5433)
- [ ] pgvector 확장 활성화
- [ ] chat_sessions 테이블 생성
- [ ] Python 연결 테스트

### 운영 준비
- [ ] 영구 볼륨 설정
- [ ] 보안 패스워드 설정
- [ ] 백업 스크립트 준비
- [ ] 모니터링 설정
- [ ] 성능 튜닝

### 정기 점검
- [ ] 디스크 사용량 확인
- [ ] 연결 수 모니터링
- [ ] 로그 확인
- [ ] 백업 상태 점검

---

📝 **작성일**: 2025-08-06  
🔄 **버전**: 1.0  
👨‍💻 **작성자**: Claude Code Assistant  
🐳 **Docker**: pgvector/pgvector:pg16