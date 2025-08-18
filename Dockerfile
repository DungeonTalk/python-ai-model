FROM python:3.13-slim

WORKDIR /app

# uv 설치 (더 빠른 패키지 매니저)
RUN pip install uv

# 의존성 파일 복사
COPY pyproject.toml uv.lock ./

# 의존성 설치
RUN uv sync --frozen

# 애플리케이션 코드 복사
COPY . .

# 포트 노출
EXPOSE 8001

# 애플리케이션 실행
CMD ["uv", "run", "uvicorn", "main_ai_only:app", "--host", "0.0.0.0", "--port", "8001"]