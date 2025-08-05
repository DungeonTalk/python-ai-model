# 🎲 던전톡 RAG MVP

TRPG(테이블탑 RPG) AI 어시스턴트 - RAG 기반 던전마스터

## 🚀 빠른 시작

### 1. 저장소 클론
```bash
git clone [repository-url]
cd dungeontalk-mvp
```

### 2. 자동 설치 (Windows) - UV 고속 버전
```bash
setup.bat
```
*UV를 사용하여 기존 pip보다 10-100배 빠른 설치*

### 3. 환경 변수 설정
1. `.env.example`을 `.env`로 복사
2. Claude API 키 입력:
```
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

### 4. 실행
```bash
# FastAPI 서버
python main.py

# 웹 UI (별도 터미널)
streamlit run streamlit_app.py
```

## 📝 접속 주소
- **FastAPI 문서**: http://localhost:8005/docs
- **Streamlit 웹UI**: http://localhost:8501

## 📚 사용법

### 문서 추가
1. `documents/` 폴더에 `.txt`, `.md`, `.csv` 파일 업로드
2. 서버 재시작시 자동 임베딩

### 질문 예시
- "근접무기 중에 좋은 게 뭐 있어?"
- "엘프 현자에 대해 알려줘"
- "황혼의 새벽 세계관 설명해줘"

## 🛠 기술 스택
- **FastAPI**: REST API 서버
- **Streamlit**: 웹 UI
- **Claude 3.5 Sonnet**: LLM
- **ChromaDB**: 벡터 데이터베이스
- **LangChain**: RAG 파이프라인

## 📋 요구사항
- Python 3.8+
- Claude API 키 (https://console.anthropic.com)
- 메모리 4GB+ 권장

## 🔧 문제 해결

### "ModuleNotFoundError" 오류
```bash
# UV 사용 (권장)
uv pip install -r requirements.txt

# 또는 기존 pip 사용
pip install -r requirements.txt
```

### UV 수동 설치 (선택사항)
```bash
pip install uv
```

### Claude API 오류
- `.env` 파일의 `ANTHROPIC_API_KEY` 확인
- API 키 잔액 확인

### 한국어 응답이 이상한 경우
- 서버 재시작
- documents 폴더에 한국어 문서 추가