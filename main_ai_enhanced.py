"""
Enhanced Main AI Server with World Type Metadata Support
세계관 메타데이터를 지원하는 향상된 AI 서버
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import sys
import time
import requests
from dotenv import load_dotenv

# Enhanced RAG Engine import
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
from rag_engine_enhanced import EnhancedRAGEngine

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

app = FastAPI(title="던전톡 Enhanced AI 응답 서비스")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙 추가
app.mount("/static", StaticFiles(directory="."), name="static")

# Enhanced RAG Engine 초기화 및 문서 로딩
try:
    enhanced_rag = EnhancedRAGEngine()
    print("[INFO] Enhanced RAG Engine 초기화 성공")
    
    # 서버 시작 시 자동으로 문서 로딩
    documents_dir = "./documents"
    if os.path.exists(documents_dir) and os.listdir(documents_dir):
        print(f"[INFO] 문서 디렉토리에서 문서 로딩 시작: {documents_dir}")
        try:
            enhanced_rag.load_documents(documents_dir)
            print(f"[INFO] ✅ 문서 로딩 완료 - {len(os.listdir(documents_dir))}개 파일 처리")
        except Exception as doc_error:
            print(f"[WARNING] 문서 로딩 실패: {doc_error}")
            print("[WARNING] 벡터 DB가 비어있을 수 있습니다. 수동으로 문서를 업로드하세요.")
    else:
        print(f"[WARNING] 문서 디렉토리가 비어있거나 존재하지 않습니다: {documents_dir}")
        
except Exception as e:
    print(f"[ERROR] Enhanced RAG Engine 초기화 실패: {e}")
    enhanced_rag = None

# Spring Boot 연동용 데이터 모델들
class ContextMessage(BaseModel):
    messageType: str  # USER, AI, SYSTEM
    senderNickname: str
    content: str
    turnNumber: int
    messageOrder: int

class EnhancedAiResponseRequest(BaseModel):
    game_id: str
    ai_game_room_id: str
    current_user: str
    current_message: str
    context_messages: List[ContextMessage] = []
    turn_number: int
    game_settings: str = ""
    world_type: str = "FANTASY"  # 세계관 추가
    doc_types: Optional[List[str]] = None  # 검색할 문서 타입 제한
    game_start_time: Optional[int] = None  # 게임 시작 시간 (Unix timestamp)
    target_duration: int = 15  # 목표 시간 (분)
    character_stats: Optional[dict] = None  # 캐릭터 스탯 정보

class EnhancedAiResponseResult(BaseModel):
    content: str
    response_time: int  # milliseconds
    world_type: str
    sources: List[dict] = []
    doc_types_used: List[str] = []
    game_time_info: Optional[dict] = None  # 게임 시간 정보

class DocumentUploadRequest(BaseModel):
    world_type: Optional[str] = None
    doc_type: Optional[str] = None
    user_tags: Optional[List[str]] = None

# Java에서 세계관 정보를 가져오는 함수
async def fetch_world_types_from_java():
    """Java API에서 세계관 목록 조회"""
    try:
        java_api_url = os.getenv("JAVA_API_BASE_URL", "http://localhost:8080")
        response = requests.get(f"{java_api_url}/api/world-types", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[WARNING] Java API에서 세계관 조회 실패: {response.status_code}")
            return []
    except Exception as e:
        print(f"[WARNING] Java API 연결 실패: {e}")
        return []

# Enhanced AI 응답 생성 엔드포인트
@app.post("/ai-response-enhanced", response_model=EnhancedAiResponseResult)
async def generate_enhanced_ai_response(request: EnhancedAiResponseRequest):
    """세계관별 특화된 AI 응답 생성 API"""
    
    if not enhanced_rag:
        raise HTTPException(status_code=500, detail="Enhanced RAG Engine이 초기화되지 않았습니다")
    
    try:
        # 캐릭터 정보 로깅
        char_info = ""
        if request.character_stats:
            char_name = request.character_stats.get('name', request.current_user)
            char_level = request.character_stats.get('level', '?')
            char_class = request.character_stats.get('characterClass', '?')
            char_info = f", 캐릭터: {char_name}(Lv.{char_level}, {char_class})"
        
        print(f"[INFO] Enhanced AI 응답 생성 - 게임방: {request.ai_game_room_id}, 세계관: {request.world_type}, 사용자: {request.current_user}{char_info}")
        
        # Enhanced RAG Engine으로 세계관별 응답 생성 (시간 관리 및 캐릭터 스탯 포함)
        result = enhanced_rag.generate_world_specific_response(
            world_type=request.world_type,
            context_messages=[msg.model_dump() for msg in request.context_messages],
            current_user=request.current_user,
            current_message=request.current_message,
            game_settings=request.game_settings,
            doc_types=request.doc_types,
            game_start_time=request.game_start_time,
            target_duration=request.target_duration,
            character_stats=request.character_stats
        )
        
        return EnhancedAiResponseResult(
            content=result["content"],
            response_time=result["response_time"],
            world_type=result["world_type"],
            sources=result["sources"],
            doc_types_used=result["doc_types_used"],
            game_time_info=result["game_time_info"]
        )
        
    except Exception as e:
        print(f"[ERROR] Enhanced AI 응답 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=f"AI 응답 생성 중 오류: {str(e)}")

# 기존 API와의 호환성을 위한 엔드포인트
@app.post("/ai-response", response_model=EnhancedAiResponseResult)
async def generate_ai_response_compatible(request: EnhancedAiResponseRequest):
    """기존 API와 호환되는 AI 응답 생성 (세계관 기본값: FANTASY)"""
    
    # 기존 요청에 세계관이 없으면 기본값 설정
    if not hasattr(request, 'world_type') or not request.world_type:
        request.world_type = "FANTASY"
    
    return await generate_enhanced_ai_response(request)

# 캐시 통계 조회 엔드포인트
@app.get("/cache-stats")
async def get_cache_stats():
    """Redis 캐시 통계 조회"""
    try:
        if enhanced_rag:
            stats = enhanced_rag.response_cache.get_stats()
            return {"success": True, "stats": stats}
        else:
            return {"success": False, "error": "RAG Engine not initialized"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"캐시 통계 조회 실패: {str(e)}")

# 문서 업로드 엔드포인트
@app.post("/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    world_type: Optional[str] = None,
    doc_type: Optional[str] = None,
    user_tags: Optional[str] = None
):
    """메타데이터와 함께 문서 업로드"""
    
    if not enhanced_rag:
        raise HTTPException(status_code=500, detail="Enhanced RAG Engine이 초기화되지 않았습니다")
    
    try:
        # 임시 파일로 저장
        temp_path = f"./temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 사용자 태그 파싱
        parsed_tags = []
        if user_tags:
            parsed_tags = [tag.strip() for tag in user_tags.split(",") if tag.strip()]
        
        # 메타데이터와 함께 문서 추가
        result = enhanced_rag.add_document_with_metadata(
            file_path=temp_path,
            world_type=world_type,
            doc_type=doc_type,
            user_tags=parsed_tags
        )
        
        # 임시 파일 삭제
        os.remove(temp_path)
        
        if result["success"]:
            return {
                "message": "문서 업로드 성공",
                "filename": file.filename,
                "chunks_added": result["chunks_added"],
                "detected_metadata": result["metadata"],
                "auto_tags": result["auto_tags"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        # 임시 파일 정리
        if os.path.exists(f"./temp_{file.filename}"):
            os.remove(f"./temp_{file.filename}")
        
        print(f"[ERROR] 문서 업로드 실패: {e}")
        raise HTTPException(status_code=500, detail=f"문서 업로드 중 오류: {str(e)}")

# 문서 재스캔 엔드포인트
@app.post("/rescan-documents")
async def rescan_documents():
    """documents 폴더를 메타데이터와 함께 재스캔"""
    
    if not enhanced_rag:
        raise HTTPException(status_code=500, detail="Enhanced RAG Engine이 초기화되지 않았습니다")
    
    try:
        result = enhanced_rag.rescan_documents_with_metadata()
        return {
            "message": "문서 재스캔 완료",
            "processed": result["processed"],
            "failed": result["failed"]
        }
    except Exception as e:
        print(f"[ERROR] 문서 재스캔 실패: {e}")
        raise HTTPException(status_code=500, detail=f"문서 재스캔 중 오류: {str(e)}")

# 벡터 DB 수동 초기화 엔드포인트 (AWS 배포용)
@app.post("/init-vectordb")
async def init_vectordb():
    """벡터 DB 수동 초기화 (AWS 배포 시 사용)"""
    
    if not enhanced_rag:
        raise HTTPException(status_code=500, detail="Enhanced RAG Engine이 초기화되지 않았습니다")
    
    try:
        documents_dir = "./documents"
        
        if not os.path.exists(documents_dir):
            raise HTTPException(status_code=404, detail="documents 디렉토리를 찾을 수 없습니다")
        
        files = os.listdir(documents_dir)
        if not files:
            raise HTTPException(status_code=404, detail="documents 디렉토리에 파일이 없습니다")
        
        print(f"[INFO] 벡터 DB 수동 초기화 시작 - {len(files)}개 파일 처리")
        
        # 문서 로딩 실행
        enhanced_rag.load_documents(documents_dir)
        
        # 초기화 결과 확인
        try:
            docs = enhanced_rag.vectorstore.similarity_search("test", k=1)
            success = len(docs) > 0
        except:
            success = False
        
        return {
            "message": "벡터 DB 초기화 완료" if success else "벡터 DB 초기화 실행됨 (결과 확인 필요)",
            "files_processed": len(files),
            "files": files,
            "initialization_success": success,
            "timestamp": time.time()
        }
        
    except Exception as e:
        print(f"[ERROR] 벡터 DB 초기화 실패: {e}")
        raise HTTPException(status_code=500, detail=f"벡터 DB 초기화 중 오류: {str(e)}")

# 세계관 목록 조회 (Java API 연동)
@app.get("/world-types")
async def get_world_types():
    """Java API에서 세계관 목록 조회"""
    world_types = await fetch_world_types_from_java()
    
    # Java API 연결 실패 시 기본값 반환
    if not world_types:
        return [
            {"code": "FANTASY", "displayName": "판타지"},
            {"code": "SF", "displayName": "SF"},
            {"code": "MODERN", "displayName": "현대"}
        ]
    
    return world_types

# 세계관별 통계 조회
@app.get("/world-stats")
async def get_world_stats():
    """세계관별 문서 통계 조회"""
    if not enhanced_rag:
        raise HTTPException(status_code=500, detail="Enhanced RAG Engine이 초기화되지 않았습니다")
    
    return enhanced_rag.get_world_type_stats()

# 벡터 DB 상태 확인 엔드포인트
@app.get("/vector-db-status")
async def vector_db_status():
    """벡터 DB 상태 및 문서 수 확인"""
    if not enhanced_rag:
        raise HTTPException(status_code=500, detail="Enhanced RAG Engine이 초기화되지 않았습니다")
    
    try:
        # 벡터스토어에서 문서 수 확인
        docs = enhanced_rag.vectorstore.similarity_search("test", k=1)
        
        # PostgreSQL에서 실제 문서 수 확인
        try:
            # 직접 PostgreSQL 쿼리로 확인
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            conn = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST', 'postgres'),
                port=int(os.getenv('POSTGRES_PORT', 5432)),
                user=os.getenv('POSTGRES_USER', 'root'),
                password=os.getenv('POSTGRES_PASSWORD', '1234'),
                database=os.getenv('POSTGRES_DB', 'dungeondb')
            )
            
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT COUNT(*) as count FROM langchain_pg_embedding;")
            result = cursor.fetchone()
            doc_count = result['count'] if result else 0
            
            cursor.close()
            conn.close()
            
        except Exception as db_error:
            doc_count = f"DB 접근 오류: {str(db_error)}"
        
        return {
            "vectorstore_available": True,
            "document_count": doc_count,
            "sample_search_results": len(docs),
            "documents_directory_exists": os.path.exists("./documents"),
            "documents_in_dir": len(os.listdir("./documents")) if os.path.exists("./documents") else 0,
            "timestamp": time.time()
        }
        
    except Exception as e:
        return {
            "vectorstore_available": False,
            "error": str(e),
            "documents_directory_exists": os.path.exists("./documents"),
            "documents_in_dir": len(os.listdir("./documents")) if os.path.exists("./documents") else 0,
            "timestamp": time.time()
        }

# 헬스체크 엔드포인트
@app.get("/health")
async def health_check():
    """서버 상태 확인"""
    return {
        "status": "healthy",
        "enhanced_rag_available": enhanced_rag is not None,
        "timestamp": time.time()
    }

# 테스트 페이지 엔드포인트
@app.get("/test")
async def test_page():
    """Enhanced RAG 테스트 페이지"""
    try:
        return FileResponse("test_enhanced_rag.html")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="테스트 페이지를 찾을 수 없습니다")

# RAG 관리 페이지 엔드포인트
@app.get("/admin")
async def admin_page():
    """RAG 데이터 관리 페이지"""
    try:
        return FileResponse("rag_admin.html")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="관리 페이지를 찾을 수 없습니다")

# 서버 정보 엔드포인트
@app.get("/")
async def root():
    """서버 정보"""
    return {
        "service": "던전톡 Enhanced AI 응답 서비스",
        "version": "2.0.0",
        "features": [
            "세계관별 문서 분리",
            "스마트 메타데이터 생성", 
            "자동 태그 추출",
            "문서 타입 자동 감지",
            "Java API 연동"
        ],
        "endpoints": {
            "ai_response": "/ai-response-enhanced",
            "document_upload": "/upload-document", 
            "document_rescan": "/rescan-documents",
            "world_types": "/world-types",
            "health": "/health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    # 서버 시작 시 문서 자동 스캔 (선택사항)
    auto_scan = os.getenv("AUTO_SCAN_ON_START", "false").lower() == "true"
    if auto_scan and enhanced_rag:
        print("[INFO] 서버 시작 시 문서 자동 스캔 실행...")
        try:
            enhanced_rag.rescan_documents_with_metadata()
        except Exception as e:
            print(f"[WARNING] 자동 스캔 실패: {e}")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)