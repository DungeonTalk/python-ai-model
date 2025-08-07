from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_postgres.vectorstores import PGVector
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
# psycopg2 대신 psycopg (v3) 사용 - 이미 langchain-postgres에 포함됨
import psycopg
from langchain_ollama import OllamaLLM
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
import os
import shutil
import glob
import hashlib
import json
from dotenv import load_dotenv

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

app = FastAPI(title="던전톡 RAG API")

class PostgreSQLSessionManager:
    """PostgreSQL 기반 세션별 대화 기록 관리 클래스"""
    
    def __init__(self):
        base_connection = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
        self.connection_string = f"{base_connection}?options=-csearch_path%3Ddungeontalk_rag"
        self._init_db()
    
    def _init_db(self):
        """데이터베이스 연결 및 테이블 초기화"""
        try:
            conn = psycopg.connect(self.connection_string)
            with conn.cursor() as cur:
                # sessions 테이블이 없으면 생성
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS chat_sessions (
                        id SERIAL PRIMARY KEY,
                        session_id VARCHAR(255) NOT NULL,
                        user_name VARCHAR(255) NOT NULL,
                        message TEXT NOT NULL,
                        response TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                conn.commit()
            conn.close()
            print("[INFO] PostgreSQL 세션 매니저 초기화 완료")
        except Exception as e:
            print(f"[ERROR] PostgreSQL 세션 매니저 초기화 실패: {e}")
    
    def get_history(self, session_id: str, limit: int = 10) -> list:
        """세션 대화 기록 조회"""
        try:
            conn = psycopg.connect(self.connection_string)
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT user_name, message, response, created_at 
                    FROM chat_sessions 
                    WHERE session_id = %s 
                    ORDER BY created_at DESC 
                    LIMIT %s
                """, (session_id, limit))
                
                results = cur.fetchall()
                history = []
                for row in results:
                    history.append({
                        "user": row[0],
                        "message": row[1],
                        "response": row[2],
                        "timestamp": row[3]
                    })
                
            conn.close()
            return list(reversed(history))  # 시간순 정렬
        except Exception as e:
            print(f"[ERROR] 세션 히스토리 조회 실패: {e}")
            return []
    
    def save_chat_record(self, session_id: str, user_name: str, message: str, response: str):
        """대화 기록 저장"""
        try:
            conn = psycopg.connect(self.connection_string)
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO chat_sessions (session_id, user_name, message, response) 
                    VALUES (%s, %s, %s, %s)
                """, (session_id, user_name, message, response))
                conn.commit()
            conn.close()
        except Exception as e:
            print(f"[ERROR] 세션 저장 실패: {e}")
    
    def get_sessions_info(self):
        """전체 세션 정보 조회"""
        try:
            conn = psycopg.connect(self.connection_string)
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT session_id, COUNT(*) as message_count, 
                           STRING_AGG(DISTINCT user_name, ', ') as users,
                           MAX(created_at) as last_activity
                    FROM chat_sessions 
                    GROUP BY session_id
                """)
                
                results = cur.fetchall()
                sessions_info = {}
                for row in results:
                    sessions_info[row[0]] = {
                        "message_count": row[1],
                        "users": row[2].split(', ') if row[2] else [],
                        "last_activity": row[3]
                    }
                
            conn.close()
            return {
                "total_sessions": len(sessions_info),
                "sessions": sessions_info
            }
        except Exception as e:
            print(f"[ERROR] 세션 정보 조회 실패: {e}")
            return {"total_sessions": 0, "sessions": {}}

# 세션 매니저 인스턴스 생성
session_manager = PostgreSQLSessionManager()

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
            self.embeddings = HuggingFaceEmbeddings(
                model_name=os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-large"),
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            print("[INFO] 로컬 HuggingFace 임베딩 사용")
        
        # PostgreSQL PGVector 사용 여부 확인
        use_postgresql = os.getenv("USE_POSTGRESQL", "false").lower() == "true"
        
        if use_postgresql:
            # PostgreSQL 연결 문자열 (스키마 분리)
            base_connection = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
            connection_string = f"{base_connection}?options=-csearch_path%3Ddungeontalk_rag"
            
            self.vectorstore = PGVector(
                embeddings=self.embeddings,
                connection=connection_string,
                collection_name="documents",
                distance_strategy="cosine"
            )
            print("[INFO] PostgreSQL PGVector 벡터스토어 사용")
        else:
            # ChromaDB 백업 사용
            self.vectorstore = Chroma(
                persist_directory="./vectorstore_openai",
                embedding_function=self.embeddings
            )
            print("[INFO] ChromaDB 벡터스토어 사용")
        
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
        else:
            self.llm = OllamaLLM(
                model="llama3.2",
                base_url="http://localhost:11434"
            )
        
        # 검색 관련 설정
        search_k = int(os.getenv("SEARCH_K", "3"))
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": search_k}),
            return_source_documents=True
        )
        
        # 파일 해시 추적을 위한 경로
        self.hash_file = "./vectorstore_openai/file_hashes.json"
        
        # 서버 시작시 자동으로 documents 폴더 스캔
        self.auto_embed_documents()
    
    def add_document(self, file_path: str):
        """문서를 벡터스토어에 추가 (다양한 인코딩 지원)"""
        # 인코딩 자동 감지 및 로드
        try:
            # UTF-8 먼저 시도
            loader = TextLoader(file_path, encoding='utf-8')
            documents = loader.load()
        except UnicodeDecodeError:
            try:
                # CP949 (한국어 Windows 기본) 시도
                loader = TextLoader(file_path, encoding='cp949')
                documents = loader.load()
                print(f"[INFO] CP949 인코딩으로 로드됨: {file_path}")
            except UnicodeDecodeError:
                try:
                    # UTF-8 with BOM 시도
                    loader = TextLoader(file_path, encoding='utf-8-sig')
                    documents = loader.load()
                    print(f"[INFO] UTF-8 BOM 인코딩으로 로드됨: {file_path}")
                except Exception as e:
                    print(f"[ERROR] 파일 인코딩을 감지할 수 없습니다 ({file_path}): {e}")
                    return
        
        chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
        chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        texts = text_splitter.split_documents(documents)
        
        self.vectorstore.add_documents(texts)
        
        # 파일 해시 업데이트
        self.update_file_hash(file_path)
    
    def query(self, question: str, session_history: list = None, current_user: str = None):
        # 이전 대화 기록을 문맥으로 구성
        context = ""
        if session_history:
            # 최근 대화 개수 설정
            recent_chat_count = int(os.getenv("RECENT_CHAT_COUNT", "5"))
            context = "\n이전 대화 기록:\n"
            for record in session_history[-recent_chat_count:]:  # 최근 N개만 사용
                context += f"- {record['user']}: {record['message']}\n"
                context += f"  GM: {record['response'][:100]}...\n"
        
        trpg_question = f"""당신은 TRPG GM입니다. 다중 플레이어 게임을 진행해주세요.

{context}

현재 발언자: {current_user}
새로운 질문/행동: {question}

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
        
        return {
            "answer": result["result"],
            "sources": [doc.page_content[:100] + "..."
                       for doc in result["source_documents"]]
        }
    
    def get_file_hash(self, file_path: str) -> str:
        """파일의 MD5 해시값을 계산합니다."""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except FileNotFoundError:
            print(f"[ERROR] 파일을 찾을 수 없습니다: {file_path}")
            return ""
        except PermissionError:
            print(f"[ERROR] 파일 접근 권한이 없습니다: {file_path}")
            return ""
        except Exception as e:
            print(f"[ERROR] 파일 해시 계산 실패 ({file_path}): {e}")
            return ""
    
    def load_file_hashes(self) -> dict:
        """저장된 파일 해시 정보를 로드합니다."""
        try:
            if os.path.exists(self.hash_file):
                with open(self.hash_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except json.JSONDecodeError as e:
            print(f"[ERROR] 해시 파일 JSON 파싱 실패: {e}")
        except UnicodeDecodeError as e:
            print(f"[ERROR] 해시 파일 인코딩 오류: {e}")
        except Exception as e:
            print(f"[ERROR] 해시 파일 로드 실패: {e}")
        return {}
    
    def save_file_hashes(self, hashes: dict):
        """파일 해시 정보를 저장합니다."""
        try:
            os.makedirs(os.path.dirname(self.hash_file), exist_ok=True)
            with open(self.hash_file, 'w', encoding='utf-8') as f:
                json.dump(hashes, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"해시 파일 저장 실패: {e}")
    
    def update_file_hash(self, file_path: str):
        """특정 파일의 해시값을 업데이트합니다."""
        hashes = self.load_file_hashes()
        hashes[file_path] = self.get_file_hash(file_path)
        self.save_file_hashes(hashes)
    
    def auto_embed_documents(self):
        """documents 폴더의 모든 파일을 자동으로 임베딩합니다."""
        documents_path = "./documents"
        if not os.path.exists(documents_path):
            os.makedirs(documents_path, exist_ok=True)
            print("[INFO] documents 폴더가 생성되었습니다.")
            return
        
        # 지원하는 파일 확장자
        supported_extensions = ['.txt', '.md', '.csv']
        
        # 기존 해시 정보 로드
        existing_hashes = self.load_file_hashes()
        
        # documents 폴더 스캔
        files_processed = 0
        files_skipped = 0
        
        print("[SCAN] documents 폴더를 스캔하고 있습니다...")
        
        for ext in supported_extensions:
            pattern = os.path.join(documents_path, f"**/*{ext}")
            for file_path in glob.glob(pattern, recursive=True):
                try:
                    # 현재 파일 해시 계산
                    current_hash = self.get_file_hash(file_path)
                    
                    # 이미 처리된 파일인지 확인
                    if file_path in existing_hashes and existing_hashes[file_path] == current_hash:
                        files_skipped += 1
                        continue
                    
                    # 새로운 파일이거나 변경된 파일이면 임베딩
                    print(f"[EMBED] 임베딩 중: {file_path}")
                    self.add_document(file_path)
                    files_processed += 1
                    
                except Exception as e:
                    print(f"[ERROR] {file_path} 처리 실패: {e}")
        
        if files_processed > 0:
            print(f"[SUCCESS] {files_processed}개 파일이 새로 임베딩되었습니다.")
        if files_skipped > 0:
            print(f"[SKIP] {files_skipped}개 파일은 이미 처리되어 건너뛰었습니다.")
        
        if files_processed == 0 and files_skipped == 0:
            print("[INFO] documents 폴더에 지원되는 파일이 없습니다. (.txt, .md, .csv)")
    
    def rescan_documents(self):
        """documents 폴더를 다시 스캔하고 변경된 파일들을 임베딩합니다."""
        self.auto_embed_documents()

rag = RAGEngine()

class ChatRequest(BaseModel):
    session_id: str
    user_name: str
    message: str

class ChatResponse(BaseModel):
    response: str
    sources: list = []
    session_id: str

def get_session_history(session_id: str) -> list:
    """세션 대화 기록 조회"""
    return session_manager.get_history(session_id)

def save_chat_record(session_id: str, user_name: str, message: str, response: str):
    """대화 기록 저장"""
    session_manager.save_chat_record(session_id, user_name, message, response)

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        print(f"[DEBUG] 채팅 요청 - 세션: {request.session_id}, 사용자: {request.user_name}")
        
        # 세션 기록 조회
        session_history = get_session_history(request.session_id)
        
        # AI 응답 생성
        result = rag.query(
            question=request.message,
            session_history=session_history,
            current_user=request.user_name
        )
        
        # 대화 기록 저장
        save_chat_record(
            session_id=request.session_id,
            user_name=request.user_name,
            message=request.message,
            response=result["answer"]
        )
        
        print(f"[DEBUG] 응답 성공 - 세션 대화 수: {len(session_manager.get_history(request.session_id))}")
        
        return ChatResponse(
            response=result["answer"],
            sources=result["sources"],
            session_id=request.session_id
        )
    except Exception as e:
        print(f"[ERROR] 채팅 처리 중 오류: {str(e)}")
        print(f"[ERROR] 오류 타입: {type(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        file_path = f"./documents/{file.filename}"
        os.makedirs("./documents", exist_ok=True)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        rag.add_document(file_path)
        
        return {"message": f"{file.filename} 업로드 완료"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/rescan")
async def rescan_documents():
    """documents 폴더를 다시 스캔하고 새로운/변경된 파일들을 임베딩합니다."""
    try:
        rag.rescan_documents()
        return {"message": "documents 폴더 재스캔 완료"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions")
async def get_active_sessions():
    """활성 세션 목록 조회"""
    return session_manager.get_sessions_info()

@app.get("/sessions/{session_id}/history")
async def get_session_history_endpoint(session_id: str):
    """특정 세션의 대화 기록 조회"""
    history = get_session_history(session_id)
    if not history:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    
    return {
        "session_id": session_id,
        "message_count": len(history),
        "history": history
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", "8000"))
    host = os.getenv("API_HOST", "0.0.0.0")
    
    print(f"[INFO] 서버 시작 - {host}:{port}")
    uvicorn.run(app, host=host, port=port)