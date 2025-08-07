#!/bin/bash

echo "던전톡 RAG MVP 설치 스크립트 (macOS/Linux)"
echo ""

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}1. Python 설치 확인 중...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python3이 설치되어 있지 않습니다.${NC}"
    echo "Homebrew로 Python을 설치하세요:"
    echo "  brew install python"
    exit 1
fi

python_version=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}Python ${python_version} 발견됨${NC}"

echo -e "${BLUE}2. UV 설치 확인 중...${NC}"
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}UV가 설치되어 있지 않습니다. UV를 설치합니다...${NC}"
    
    # macOS에서 UV 설치
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # Homebrew로 설치 시도
        if command -v brew &> /dev/null; then
            echo "Homebrew로 UV 설치 중..."
            brew install uv
        else
            # curl로 직접 설치
            echo "curl로 UV 설치 중..."
            curl -LsSf https://astral.sh/uv/install.sh | sh
            export PATH="$HOME/.cargo/bin:$PATH"
        fi
    else
        # Linux
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
    fi
    
    # 설치 확인
    if ! command -v uv &> /dev/null; then
        echo -e "${RED}UV 설치에 실패했습니다. 수동으로 설치해주세요:${NC}"
        echo "  pip install uv"
        exit 1
    fi
fi

uv_version=$(uv --version)
echo -e "${GREEN}${uv_version} 발견됨${NC}"

echo -e "${BLUE}3. 프로젝트 의존성 설치 중 (pyproject.toml 기반)...${NC}"
uv sync

echo -e "${BLUE}4. 환경 변수 파일 확인 중...${NC}"
if [ ! -f .env ]; then
    echo -e "${YELLOW}.env 파일이 없습니다.${NC}"
    if [ -f .env.example ]; then
        echo "  .env.example을 .env로 복사합니다..."
        cp .env.example .env
        echo -e "${RED}API 키를 설정한 후 다시 실행하세요:${NC}"
        echo "  nano .env"
    else
        echo -e "${RED}.env.example 파일이 없습니다. 수동으로 .env 파일을 생성하세요.${NC}"
    fi
else
    echo -e "${GREEN}.env 파일 발견됨${NC}"
fi

echo -e "${BLUE}5. documents 폴더 확인 중...${NC}"
if [ ! -d "documents" ]; then
    mkdir documents
    echo -e "${GREEN}documents 폴더 생성됨${NC}"
else
    echo -e "${GREEN}documents 폴더 발견됨${NC}"
fi

echo ""
echo -e "${GREEN}설치 완료! 다음 명령어로 실행하세요:${NC}"
echo ""
echo -e "${BLUE}FastAPI 서버 실행:${NC}"
echo "  uv run python main.py"
echo ""
echo -e "${BLUE}Streamlit 웹 UI 실행:${NC}"  
echo "  uv run streamlit run streamlit_app.py"
echo ""
echo -e "${BLUE}PostgreSQL 설정 (필요시):${NC}"
echo "  docker run -d --name postgres-pgvector \\"
echo "    -e POSTGRES_USER=root -e POSTGRES_PASSWORD=1234 \\"
echo "    -e POSTGRES_DB=dungeondb -p 5432:5432 \\"
echo "    pgvector/pgvector:pg17"
echo ""
echo -e "${YELLOW}참고: API 키 설정을 잊지 마세요!${NC}"
echo "  nano .env"
echo ""