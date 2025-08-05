from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain_anthropic import ChatAnthropic
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
import os
import shutil
import glob
import hashlib
import json
import re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="던전톡 RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class RAGEngine:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="intfloat/multilingual-e5-large",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        self.vectorstore = Chroma(
            persist_directory="./vectorstore_new",
            embedding_function=self.embeddings
        )
        
        # 환경변수에서 LLM 제공자 선택
        llm_provider = os.getenv("LLM_PROVIDER", "ollama").lower()
        
        if llm_provider == "claude":
            self.llm = ChatAnthropic(
                model=os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022"),
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                temperature=0.7,
                max_tokens=2000
            )
        else:
            self.llm = OllamaLLM(
                model="llama3.2",
                base_url="http://localhost:11434"
            )
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 3}),
            return_source_documents=True
        )
        
        # 파일 해시 추적을 위한 경로
        self.hash_file = "./vectorstore_new/file_hashes.json"
        
        # 서버 시작시 자동으로 documents 폴더 스캔
        self.auto_embed_documents()
    
    def add_document(self, file_path: str):
        loader = TextLoader(file_path, encoding='utf-8')
        documents = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        texts = text_splitter.split_documents(documents)
        
        self.vectorstore.add_documents(texts)
        
        # 파일 해시 업데이트
        self.update_file_hash(file_path)
    
    def query(self, question: str):
        trpg_question = f"""당신은 TRPG 던전마스터입니다. 게임을 진행해주세요.

{question}"""
        
        result = self.qa_chain({"query": trpg_question})
        
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
        except Exception:
            return ""
    
    def load_file_hashes(self) -> dict:
        """저장된 파일 해시 정보를 로드합니다."""
        try:
            if os.path.exists(self.hash_file):
                with open(self.hash_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
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
    message: str

class ChatResponse(BaseModel):
    response: str
    sources: list = []

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        result = rag.query(request.message)
        return ChatResponse(
            response=result["answer"],
            sources=result["sources"]
        )
    except Exception as e:
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)