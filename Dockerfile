FROM python:3.13-slim

WORKDIR /app

# 시스템 패키지 최소 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# uv 설치 (더 빠른 패키지 매니저)
RUN pip install --no-cache-dir uv

# 의존성 파일만 먼저 복사 (캐시 최적화)
COPY pyproject.toml ./

# 의존성 설치 (개발 의존성 제외, 캐시 정리)
RUN uv sync --no-dev && \
    uv cache clean

# 애플리케이션 코드만 선택적 복사
COPY main_ai_only.py ./
COPY documents/ ./documents/

# 불필요한 파일 정리
RUN find . -type d -name __pycache__ -delete && \
    find . -type f -name "*.pyc" -delete

# 포트 노출
EXPOSE 8001

# 애플리케이션 실행
CMD ["uv", "run", "python", "main_ai_only.py"]