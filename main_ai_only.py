from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_postgres.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import os
import time
from dotenv import load_dotenv
from typing import List

load_dotenv()

def validate_environment():
    """환경변수 검증"""
    llm_provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    
    if llm_provider == "claude":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key or api_key.startswith("sk-ant-api03-여기에"):
            raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았거나 예시 값입니다.")
    elif llm_provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY가 설정되지 않았습니다.")
    
    print(f"[INFO] 환경변수 검증 완료 - LLM Provider: {llm_provider}")

# 환경변수 검증
try:
    validate_environment()
except ValueError as e:
    print(f"[ERROR] {e}")
    print("[ERROR] .env 파일을 확인하고 올바른 API 키를 설정해주세요.")
    exit(1)

app = FastAPI(title="던전톡 AI 응답 서비스")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class RAGEngine:
    def __init__(self):
        # 원격 임베딩 사용 여부 확인
        use_remote = os.getenv("USE_REMOTE_EMBEDDINGS", "false").lower() == "true"
        
        if use_remote:
            self.embeddings = OpenAIEmbeddings(
                model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
                api_key=os.getenv("OPENAI_API_KEY")
            ) 
            print("[INFO] OpenAI 원격 임베딩 사용")
        else:
            # HuggingFace 임베딩 제거됨 - OpenAI만 사용
            print("[ERROR] 로컬 임베딩이 비활성화되었습니다. USE_REMOTE_EMBEDDINGS=true로 설정하세요.")
            raise ValueError("로컬 임베딩 지원이 제거되었습니다. OpenAI 임베딩을 사용하세요.")
        
        # PostgreSQL PGVector 벡터스토어 사용 (재시도 로직 포함)
        base_connection = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
        connection_string = f"{base_connection}?options=-csearch_path%3Ddungeontalk_rag%2Cpublic"
        
        # PostgreSQL 연결 재시도
        max_retries = 5
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                self.vectorstore = PGVector(
                    embeddings=self.embeddings,
                    connection=connection_string,
                    collection_name="documents",
                    distance_strategy="cosine"
                )
                print("[INFO] PostgreSQL PGVector 벡터스토어 연결 성공")
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    print(f"[ERROR] PostgreSQL 연결 실패: {e}")
                    raise
        
        # 환경변수에서 LLM 제공자 선택
        llm_provider = os.getenv("LLM_PROVIDER", "ollama").lower()
        
        if llm_provider == "claude":
            self.llm = ChatAnthropic(
                model=os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022"),
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
                max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2000"))
            )
        elif llm_provider == "deepseek":
            self.llm = ChatOpenAI(
                model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url="https://api.deepseek.com",
                temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
                max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2000"))
            )
        elif llm_provider == "openai":
            self.llm = ChatOpenAI(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                api_key=os.getenv("OPENAI_API_KEY"),
                temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
                max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2000"))
            )
        else:
            # 기본값을 deepseek으로 설정
            print("[WARNING] 지원되지 않는 LLM 제공자입니다. DeepSeek을 사용합니다.")
            self.llm = ChatOpenAI(
                model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url="https://api.deepseek.com",
                temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
                max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2000"))
            )
        
        # 검색 관련 설정
        search_k = int(os.getenv("SEARCH_K", "3"))
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": search_k}),
            return_source_documents=True
        )
        
        
    
    def add_document(self, file_path: str):
        """문서를 벡터스토어에 추가 (다양한 인코딩 지원)"""
        # 인코딩 자동 감지 및 로드
        content = None
        try:
            # UTF-8 먼저 시도
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                # CP949 (한국어 Windows 기본) 시도
                with open(file_path, 'r', encoding='cp949') as f:
                    content = f.read()
                print(f"[INFO] CP949 인코딩으로 로드됨: {file_path}")
            except UnicodeDecodeError:
                try:
                    # UTF-8 with BOM 시도
                    with open(file_path, 'r', encoding='utf-8-sig') as f:
                        content = f.read()
                    print(f"[INFO] UTF-8 BOM 인코딩으로 로드됨: {file_path}")
                except Exception as e:
                    print(f"[ERROR] 파일 인코딩을 감지할 수 없습니다 ({file_path}): {e}")
                    return
        
        if not content:
            print(f"[ERROR] 파일 내용이 비어있습니다: {file_path}")
            return
            
        # Document 객체 생성
        documents = [Document(page_content=content, metadata={"source": file_path})]
        
        chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
        chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        texts = text_splitter.split_documents(documents)
        
        self.vectorstore.add_documents(texts)
        
    
    def generate_ai_response(self, context_messages: List[dict], current_user: str, current_message: str):
        """Spring Boot에서 전달받은 컨텍스트로 AI 응답 생성"""
        start_time = time.time()
        
        # 컨텍스트 구성
        context = ""
        if context_messages:
            context = "\n이전 대화 기록:\n"
            for msg in context_messages:
                if msg.get('messageType') == 'USER':
                    context += f"- {msg.get('senderNickname')}: {msg.get('content')}\n"
                elif msg.get('messageType') == 'AI':
                    context += f"  GM: {msg.get('content')[:150]}...\n"
        
        trpg_question = f"""당신은 TRPG GM입니다. 다중 플레이어 게임을 진행해주세요.

{context}

현재 발언자: {current_user}
새로운 질문/행동: {current_message}

# 답변 형식 규칙:
1. 이전 대화 맥락을 고려하여 일관성 있게 답변해주세요
2. 현재 발언자({current_user})의 행동에 초점을 맞춰 답변해주세요
3. 다른 파티원들도 고려한 상황 묘사를 해주세요
4. 상황을 생생하게 묘사하고, 플레이어의 행동에 따라 스토리를 전개시킵니다
5. 각 세계관의 분위기에 맞는 몰입감 있는 롤플레잉을 제공합니다
6. 문장과 문장 사이에는 적절한 줄바꿈을 넣어주세요
7. 긴 설명은 문단으로 나누어 가독성을 높여주세요
8. 중요한 정보나 선택지는 별도 줄로 구분해주세요
9. 상황 묘사와 대화는 구분해서 작성해주세요
10. 필요시 다른 파티원들에게도 행동을 촉구해주세요 """
        
        result = self.qa_chain.invoke({"query": trpg_question})
        
        end_time = time.time()
        response_time = int((end_time - start_time) * 1000)  # 밀리초
        
        return {
            "content": result["result"],
            "response_time": response_time,
            "sources": [doc.page_content[:100] + "..."
                       for doc in result["source_documents"]]
        }
    
    def rescan_documents(self):
        """documents 폴더를 다시 스캔하고 새로운 파일들을 임베딩합니다."""
        documents_path = "./documents"
        if not os.path.exists(documents_path):
            os.makedirs(documents_path, exist_ok=True)
            print("[INFO] documents 폴더가 생성되었습니다.")
            return
        
        # 지원하는 파일 확장자
        supported_extensions = ['.txt', '.md', '.csv']
        files_processed = 0
        
        print("[SCAN] documents 폴더를 스캔하고 있습니다...")
        
        import glob
        for ext in supported_extensions:
            pattern = os.path.join(documents_path, f"**/*{ext}")
            for file_path in glob.glob(pattern, recursive=True):
                try:
                    print(f"[EMBED] 임베딩 중: {file_path}")
                    self.add_document(file_path)
                    files_processed += 1
                except Exception as e:
                    print(f"[ERROR] {file_path} 처리 실패: {e}")
        
        if files_processed > 0:
            print(f"[SUCCESS] {files_processed}개 파일이 임베딩되었습니다.")
        else:
            print("[INFO] documents 폴더에 지원되는 파일이 없습니다. (.txt, .md, .csv)")

rag = RAGEngine()

# Spring Boot 연동용 데이터 모델들
class ContextMessage(BaseModel):
    messageType: str  # USER, AI, SYSTEM
    senderNickname: str
    content: str
    turnNumber: int
    messageOrder: int

class AiResponseRequest(BaseModel):
    game_id: str
    ai_game_room_id: str
    current_user: str
    current_message: str
    context_messages: List[ContextMessage] = []
    turn_number: int

class AiResponseResult(BaseModel):
    content: str
    response_time: int  # milliseconds
    sources: List[str] = []

# Spring Boot에서 호출하는 AI 응답 생성 엔드포인트
@app.post("/ai-response", response_model=AiResponseResult)
async def generate_ai_response(request: AiResponseRequest):
    """Spring Boot AiResponseController에서 호출하는 AI 응답 생성 API"""
    try:
        print(f"[INFO] AI 응답 생성 요청 - 게임방: {request.ai_game_room_id}, 사용자: {request.current_user}, 턴: {request.turn_number}")
        
        # AI 응답 생성
        result = rag.generate_ai_response(
            context_messages=[msg.dict() for msg in request.context_messages],
            current_user=request.current_user,
            current_message=request.current_message
        )
        
        print(f"[INFO] AI 응답 생성 완료 - 응답시간: {result['response_time']}ms, 소스: {len(result['sources'])}개")
        
        return AiResponseResult(
            content=result["content"],
            response_time=result["response_time"],
            sources=result["sources"]
        )
        
    except Exception as e:
        print(f"[ERROR] AI 응답 생성 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI 응답 생성 실패: {str(e)}")


@app.post("/rescan")
async def rescan_documents():
    """documents 폴더를 다시 스캔하고 새로운/변경된 파일들을 임베딩"""
    try:
        rag.rescan_documents()
        return {"message": "documents 폴더 재스캔 완료"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """서비스 상태 확인"""
    return {
        "status": "healthy",
        "service": "dungeontalk-ai-service",
        "llm_provider": os.getenv("LLM_PROVIDER", "ollama")
    }

@app.get("/")
async def root():
    """API 정보"""
    return {
        "service": "던전톡 AI 응답 서비스",
        "version": "2.0.0",
        "description": "Spring Boot와 연동되는 AI 응답 전용 서비스",
        "endpoints": {
            "ai_response": "/ai-response",
            "rescan": "/rescan",
            "health": "/health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("AI_SERVICE_PORT", "8001"))  # 포트 변경
    host = os.getenv("AI_SERVICE_HOST", "0.0.0.0")
    
    print(f"[INFO] AI 서비스 시작 - {host}:{port}")
    print("[INFO] Spring Boot와 연동되는 AI 응답 전용 서비스")
    uvicorn.run(app, host=host, port=port)