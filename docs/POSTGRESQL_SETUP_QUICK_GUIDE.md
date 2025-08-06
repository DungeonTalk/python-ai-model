# PostgreSQL pgvector 빠른 설정 가이드

다른 프로젝트의 PostgreSQL을 pgvector로 업그레이드하고 스키마를 분리하는 간단한 설정 가이드입니다.

## 🚀 빠른 설정 단계

### 1. 다른 프로젝트 Docker Compose 수정

**파일**: `docker-compose.yml`
```yaml
services:
  postgres:
    image: pgvector/pgvector:pg17  # ← 이 부분만 변경
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

### 2. 컨테이너 재시작

```bash
# 기존 컨테이너 중지
docker-compose down

# 새 이미지로 시작
docker-compose up -d
```

### 3. PostgreSQL 스키마 설정

```bash
# PostgreSQL 접속 (컨테이너명: dungeontalk-db-postgres-1)
docker exec -it dungeontalk-db-postgres-1 psql -U root -d dungeondb
```

PostgreSQL 프롬프트에서 실행:
```sql
-- 스키마 생성
CREATE SCHEMA IF NOT EXISTS dungeontalk_rag;

-- pgvector 확장 설치
CREATE EXTENSION IF NOT EXISTS vector;

-- 확인 (선택사항)
\dn  -- 스키마 목록
\dx  -- 확장 목록

-- 종료
\q
```

### 4. 현재 프로젝트 설정

**이미 완료됨** ✅
- `.env` 파일 수정됨 (포트: 5432, DB: dungeondb, 사용자: root/1234)
- `main.py` 스키마 분리 설정 추가됨

### 5. 연결 테스트

```bash
# 현재 프로젝트에서 테스트
python main.py
```

## 📋 설정 요약

| 항목 | 기존 | 변경 후 |
|------|------|---------|
| Docker 이미지 | `postgres:17-alpine` | `pgvector/pgvector:pg17` |
| 포트 | 5433 | 5432 |
| 데이터베이스 | `rag_db` | `dungeondb` |
| 사용자 | `postgres/postgres` | `root/1234` |
| 스키마 | 기본 | `dungeontalk_rag` |

## 🔧 기능

### RDB + Vector DB 통합
- **일반 관계형 데이터**: 테이블, 조인, 트랜잭션
- **벡터 검색**: 임베딩 저장, 유사도 검색, RAG

### 스키마 분리 장점
- 다른 프로젝트와 데이터 격리
- 테이블명 충돌 방지
- 권한 관리 용이

## ✅ 완료 확인

1. **Docker 컨테이너 상태**
   ```bash
   docker ps | grep postgres
   ```

2. **스키마 확인**
   ```sql
   SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'dungeontalk_rag';
   ```

3. **pgvector 확장 확인**
   ```sql
   SELECT * FROM pg_extension WHERE extname = 'vector';
   ```

4. **애플리케이션 테스트**
   ```bash
   python main.py
   ```

## 🚨 문제 해결

### 연결 실패
```
psycopg2.OperationalError: connection to server failed
```
- PostgreSQL 컨테이너 실행 상태 확인: `docker ps`
- 포트 충돌 확인: `netstat -an | grep 5432`

### pgvector 확장 오류
```
psycopg2.errors.UndefinedObject: type "vector" does not exist
```
- pgvector 확장 재설치: `CREATE EXTENSION vector;`
- Docker 이미지 확인: `pgvector/pgvector:pg17`

### 스키마 권한 오류
```
permission denied for schema dungeontalk_rag
```
- 스키마 권한 부여: `GRANT ALL PRIVILEGES ON SCHEMA dungeontalk_rag TO root;`

## 🎯 다음 단계

설정 완료 후:
1. 문서 업로드 테스트
2. 벡터 검색 기능 확인
3. RAG 시스템 성능 테스트

---

**Note**: 이 설정으로 하나의 PostgreSQL에서 관계형 데이터와 벡터 검색을 모두 처리할 수 있습니다.