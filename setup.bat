@echo off
echo 던전톡 RAG MVP 설치 스크립트 (UV 고속 버전)
echo.

echo 1. UV 설치 확인 중...
uv --version >nul 2>&1
if errorlevel 1 (
    echo UV가 설치되어 있지 않습니다. UV를 설치합니다...
    pip install uv
    if errorlevel 1 (
        echo Python이 설치되어 있지 않습니다. Python 3.8+ 설치 후 다시 실행하세요.
        pause
        exit /b 1
    )
)

echo 2. 가상환경 생성 중 (UV 고속)...
uv venv

echo 3. 패키지 설치 중 (UV 터보 모드)...
uv pip install -r requirements.txt

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
echo   python main.py       (FastAPI 서버)
echo   streamlit run streamlit_app.py  (웹 UI)
echo.
pause