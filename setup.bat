@echo off
echo 던전톡 RAG MVP 설치 스크립트 (UV 최신 버전)
echo.

echo 1. UV 설치 확인 중...
uv --version >nul 2>&1
if errorlevel 1 (
    echo UV가 설치되어 있지 않습니다. UV를 설치합니다...
    echo PowerShell에서 다음 명령어를 실행하세요:
    echo irm https://astral.sh/uv/install.ps1 ^| iex
    pause
    exit /b 1
)

echo 2. 프로젝트 의존성 설치 중 (pyproject.toml 기반)...
uv sync

echo 3. 환경 변수 파일 확인 중...
if not exist .env (
    echo .env 파일이 없습니다. .env.example을 참고하여 .env 파일을 생성하세요.
    copy .env.example .env
    echo ANTHROPIC_API_KEY를 설정한 후 다시 실행하세요.
    pause
    exit /b 1
)

echo 4. documents 폴더 확인 중...
if not exist documents mkdir documents

echo.
echo 설치 완료! 다음 명령어로 실행하세요:
echo   uv run python main.py                  (FastAPI 서버)
echo   uv run streamlit run streamlit_app.py  (웹 UI)
echo.
echo PostgreSQL 설정이 필요하다면:
echo   docker run -d --name postgres-pgvector -e POSTGRES_USER=root -e POSTGRES_PASSWORD=1234 -e POSTGRES_DB=dungeondb -p 5432:5432 pgvector/pgvector:pg17
echo.
pause