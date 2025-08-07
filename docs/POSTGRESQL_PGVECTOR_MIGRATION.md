# PostgreSQL pgvector 마이그레이션 가이드

이 가이드는 기존 PostgreSQL을 pgvector가 포함된 PostgreSQL로 마이그레이션하고 스키마를 분리하는 방법을 설명합니다.

## 개요

- **기존**: `postgres:17-alpine` (pgvector 미포함)
- **변경**: `pgvector/pgvector:pg17` (pgvector 포함)
- **스키마 분리**: `dungeondb` 내 `dungeontalk_rag` 스키마 사용

## 1. 다른 프로젝트 Docker Compose 수정

### 1.1 기존 설정
```yaml
services:
  postgres:
    image: postgres:17-alpine
    ports:
      - "5432:5432"
    environment:
      TZ: Asia/Seoul
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: dungeondb
    volumes:
      - ./postgres/data:/var/lib/postgresql/data
```

### 1.2 변경된 설정
```yaml
services:
  postgres:
    image: pgvector/pgvector:pg17  # 🔄 변경된 부분
    ports:
      - "5432:5432"
    environment:
      TZ: Asia/Seoul
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: dungeondb
    volumes:
      - ./postgres/data:/var/lib/postgresql/data
```

## 2. 현재 프로젝트 환경 설정

### 2.1 .env 파일 수정

**기존 설정:**
```env
# PostgreSQL + pgvector 설정
USE_POSTGRESQL=true
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DB=rag_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

**새로운 설정:**
```env
# PostgreSQL + pgvector 설정
USE_POSTGRESQL=true
POSTGRES_HOST=localhost
POSTGRES_PORT=5432          # 🔄 5433 → 5432
POSTGRES_DB=dungeondb       # 🔄 rag_db → dungeondb
POSTGRES_USER=root          # 🔄 postgres → root
POSTGRES_PASSWORD=1234      # 🔄 postgres → 1234
```

## 3. PostgreSQL 스키마 설정

### 3.1 스키마 및 확장 생성
PostgreSQL에 접속하여 다음 SQL을 실행합니다:

```sql
-- dungeontalk_rag 스키마 생성
CREATE SCHEMA IF NOT EXISTS dungeontalk_rag;

-- pgvector 확장 설치 (전체 데이터베이스에 적용)
CREATE EXTENSION IF NOT EXISTS vector;

-- 스키마 권한 부여 (필요시)
GRANT ALL PRIVILEGES ON SCHEMA dungeontalk_rag TO root;
```

### 3.2 PostgreSQL 접속 방법
```bash
# Docker 컨테이너를 통한 접속
docker exec -it <postgres_container_name> psql -U root -d dungeondb

# 또는 호스트에서 직접 접속
psql -h localhost -p 5432 -U root -d dungeondb
```

## 4. 애플리케이션 코드 수정

### 4.1 main.py 수정 (스키마 분리)

**PostgreSQLSessionManager 클래스:**
```python
def __init__(self):
    # 스키마를 포함한 연결 문자열
    base_connection = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    self.connection_string = f"{base_connection}?options=-csearch_path%3Ddungeontalk_rag"
    self._init_db()
```

**RAGEngine 클래스:**
```python
# PostgreSQL 연결 문자열 (스키마 포함)
base_connection = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
connection_string = f"{base_connection}?options=-csearch_path%3Ddungeontalk_rag"

self.vectorstore = PGVector(
    embeddings=self.embeddings,
    connection_string=connection_string,
    collection_name="documents",
    distance_strategy="cosine"
)
```

## 5. 실행 순서

### 5.1 마이그레이션 단계
1. **기존 컨테이너 중지**
   ```bash
   docker-compose down
   ```

2. **docker-compose.yml 파일 수정**
   - PostgreSQL 이미지를 `pgvector/pgvector:pg17`로 변경

3. **새 컨테이너 시작**
   ```bash
   docker-compose up -d
   ```

4. **PostgreSQL 스키마 설정**
   ```bash
   docker exec -it <postgres_container> psql -U root -d dungeondb
   ```
   ```sql
   CREATE SCHEMA IF NOT EXISTS dungeontalk_rag;
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

5. **현재 프로젝트 .env 파일 수정**
   - 연결 정보를 새로운 PostgreSQL에 맞게 수정

6. **애플리케이션 실행 및 테스트**
   ```bash
   # uv 환경에서 실행
   uv run python main.py
   ```

6. **애플리케이션 코드 수정**
   - `main.py`에서 스키마 분리 설정 추가

7. **연결 테스트**
   ```bash
   python main.py
   ```

## 6. 검증 방법

### 6.1 PostgreSQL 연결 확인
```python
import psycopg2

# 연결 테스트
try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="dungeondb",
        user="root",
        password="1234"
    )
    print("✅ PostgreSQL 연결 성공")
    conn.close()
except Exception as e:
    print(f"❌ 연결 실패: {e}")
```

### 6.2 pgvector 확장 확인
```sql
-- pgvector 확장 설치 확인
SELECT * FROM pg_extension WHERE extname = 'vector';

-- 스키마 확인
SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'dungeontalk_rag';
```

### 6.3 벡터스토어 테스트
```python
from main import RAGEngine

# RAG 엔진 초기화 테스트
try:
    rag = RAGEngine()
    print("✅ RAG 엔진 초기화 성공")
except Exception as e:
    print(f"❌ RAG 엔진 초기화 실패: {e}")
```

## 7. 문제 해결

### 7.1 자주 발생하는 오류

**연결 거부 오류:**
```
psycopg2.OperationalError: connection to server at "localhost" (127.0.0.1), port 5432 failed: Connection refused
```
- **해결**: PostgreSQL 컨테이너가 실행 중인지 확인
- **명령**: `docker ps | grep postgres`

**pgvector 확장 없음:**
```
psycopg2.errors.UndefinedObject: type "vector" does not exist
```
- **해결**: `CREATE EXTENSION vector;` 실행
- **확인**: `SELECT * FROM pg_extension WHERE extname = 'vector';`

**스키마 권한 오류:**
```
psycopg2.errors.InsufficientPrivilege: permission denied for schema dungeontalk_rag
```
- **해결**: `GRANT ALL PRIVILEGES ON SCHEMA dungeontalk_rag TO root;`

## 8. 이전 설정 백업

마이그레이션 전에 기존 데이터를 백업하세요:

```bash
# ChromaDB 벡터스토어 백업 (필요시)
cp -r vectorstore_openai vectorstore_openai_backup

# 환경 설정 백업
cp .env .env.backup
```

## 완료 확인

✅ PostgreSQL pgvector 이미지로 변경  
✅ 스키마 분리 설정 완료  
✅ 환경 변수 설정 업데이트  
✅ 애플리케이션 코드 수정  
✅ 연결 테스트 성공  

이제 다른 프로젝트의 PostgreSQL과 스키마를 분리하여 안전하게 사용할 수 있습니다.