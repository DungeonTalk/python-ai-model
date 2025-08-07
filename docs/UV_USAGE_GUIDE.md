# UV 환경 사용법 가이드

이 문서는 DungeonTalk MVP 프로젝트를 uv 환경에서 사용하는 방법을 설명합니다.

## uv란?

`uv`는 Python의 새로운 패키지 관리자로, 기존 pip + venv보다 훨씬 빠르고 편리합니다.
- 속도: pip보다 10-100배 빠름
- 자동 가상환경 관리
- 의존성 잠금 (package-lock.json과 유사)
- 프로젝트 기반 관리

## 1. uv 설치

### Windows (PowerShell)
```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

### macOS/Linux
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 설치 확인
```bash
uv --version
```

## 2. 프로젝트 설정

### 새로운 환경에서 시작하기
```bash
# 프로젝트 클론
git clone <repository-url>
cd dungeontalk-mvp

# uv로 의존성 자동 설치 (pyproject.toml 기반)
uv sync
```

### 기존 .venv에서 uv로 전환 (이미 완료됨)
```bash
# uv 프로젝트 초기화 (이미 완료됨)
uv init --app

# requirements.txt의 패키지들을 uv로 추가 (이미 완료됨)
uv add fastapi uvicorn[standard] pydantic python-multipart langchain langchain-community langchain-anthropic langchain-openai langchain-huggingface sentence-transformers langchain-postgres psycopg2-binary python-dotenv

# 기존 .venv 삭제 (선택사항)
rm -rf .venv
```

## 3. 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 설정하세요:

```env
# PostgreSQL + pgvector 설정
USE_POSTGRESQL=true
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=dungeondb
POSTGRES_USER=root
POSTGRES_PASSWORD=1234

# OpenAI 임베딩 설정
USE_REMOTE_EMBEDDINGS=true
OPENAI_API_KEY=your-openai-api-key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# LLM 제공자 설정
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_MODEL=deepseek-chat

# Claude 백업 설정
ANTHROPIC_API_KEY=your-claude-api-key
CLAUDE_MODEL=claude-3-haiku-20240307

# 문서 경로
DOCUMENTS_PATH=./documents
```

## 4. PostgreSQL 데이터베이스 설정

### Docker로 PostgreSQL + pgvector 실행
```bash
# PostgreSQL 컨테이너 실행 (이미 실행중이라면 건너뛰기)
docker run -d \
  --name postgres-pgvector \
  -e POSTGRES_USER=root \
  -e POSTGRES_PASSWORD=1234 \
  -e POSTGRES_DB=dungeondb \
  -p 5432:5432 \
  pgvector/pgvector:pg17
```

### 스키마 및 Extension 설정 (최초 한 번만)
```python
# Python으로 스키마 생성
python -c "
import psycopg2
conn = psycopg2.connect('postgresql://root:1234@localhost:5432/dungeondb')
cur = conn.cursor()
cur.execute('CREATE SCHEMA IF NOT EXISTS dungeontalk_rag;')
cur.execute('CREATE EXTENSION IF NOT EXISTS vector SCHEMA public;')
conn.commit()
conn.close()
print('PostgreSQL 설정 완료')
"
```

## 5. 애플리케이션 실행

### 기본 실행 방법
```bash
uv run python main.py
```

### 개발 모드로 실행
```bash
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 6. 주요 uv 명령어

### 패키지 관리
```bash
# 새 패키지 추가
uv add requests

# 개발 의존성 추가
uv add pytest --dev

# 패키지 제거
uv remove requests

# 의존성 동기화 (새로운 환경에서)
uv sync

# 의존성 업데이트
uv lock --upgrade
```

### 실행 명령어
```bash
# Python 스크립트 실행
uv run python script.py

# 모듈 실행
uv run -m pytest

# 직접 명령어 실행
uv run uvicorn main:app --reload
```

### 가상환경 관리
```bash
# 가상환경 셸 진입
uv shell

# 가상환경에서 나가기
exit

# 가상환경 정보 확인
uv python list
```

## 7. 파일 구조

```
dungeontalk-mvp/
├── pyproject.toml          # 프로젝트 설정 및 의존성 (package.json 역할)
├── uv.lock                 # 의존성 잠금 파일 (package-lock.json 역할)
├── .env                    # 환경 변수
├── main.py                 # 메인 애플리케이션
├── documents/              # RAG용 문서들
├── docs/                   # 문서들
└── .venv/                  # 가상환경 (자동 생성)
```

## 8. 배포 및 프로덕션

### Docker 사용시
```dockerfile
FROM python:3.13-slim

# uv 설치
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 프로젝트 복사
COPY . /app
WORKDIR /app

# 의존성 설치
RUN uv sync --frozen

# 실행
CMD ["uv", "run", "python", "main.py"]
```

### requirements.txt 생성 (호환성용)
```bash
# uv에서 requirements.txt 생성
uv export --format requirements-txt --output-file requirements.txt
```

## 9. 문제 해결

### 일반적인 문제들

**Q: `uv: command not found`**
```bash
# PATH 확인 및 재로그인
source ~/.bashrc  # Linux/macOS
# 또는 PowerShell 재시작 (Windows)
```

**Q: 패키지 설치 실패**
```bash
# 캐시 클리어
uv cache clean

# 가상환경 재생성
rm -rf .venv
uv sync
```

**Q: PostgreSQL 연결 오류**
```bash
# Docker 컨테이너 상태 확인
docker ps

# PostgreSQL 재시작
docker restart postgres-pgvector
```

## 10. 기존 pip/venv 사용자를 위한 비교

| 작업 | 기존 방식 | uv 방식 |
|------|-----------|---------|
| 가상환경 생성 | `python -m venv .venv` | `uv init` (자동) |
| 가상환경 활성화 | `.venv/Scripts/activate` | 필요없음 |
| 패키지 설치 | `pip install package` | `uv add package` |
| 의존성 파일 | `requirements.txt` | `pyproject.toml` |
| 의존성 설치 | `pip install -r requirements.txt` | `uv sync` |
| 실행 | `python main.py` | `uv run python main.py` |

## 11. 추가 자료

- [uv 공식 문서](https://docs.astral.sh/uv/)
- [pyproject.toml 가이드](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- [uv vs pip 성능 비교](https://astral.sh/blog/uv)

---

**주의**: 이 가이드는 DungeonTalk MVP 프로젝트에 특화되어 작성되었습니다. 다른 프로젝트에서는 설정이 다를 수 있습니다.