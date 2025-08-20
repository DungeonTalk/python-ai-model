"""
Enhanced RAG Engine with World Type Metadata Support
세계관 메타데이터 기반의 향상된 RAG 엔진
"""

import os
import sys
import time
import json
import requests
from typing import List, Dict, Optional
from pathlib import Path

# utils 디렉토리를 Python path에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from langchain_postgres.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from dotenv import load_dotenv

from metadata_generator import MetadataGenerator

load_dotenv()

class EnhancedRAGEngine:
    """메타데이터 기반 세계관 분리를 지원하는 향상된 RAG 엔진"""
    
    def __init__(self):
        # 임베딩 설정
        use_remote = os.getenv("USE_REMOTE_EMBEDDINGS", "false").lower() == "true"
        
        if use_remote:
            self.embeddings = OpenAIEmbeddings(
                model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
                api_key=os.getenv("OPENAI_API_KEY")
            ) 
            print("[INFO] OpenAI 원격 임베딩 사용")
        else:
            print("[ERROR] 로컬 임베딩이 비활성화되었습니다. USE_REMOTE_EMBEDDINGS=true로 설정하세요.")
            raise ValueError("로컬 임베딩 지원이 제거되었습니다. OpenAI 임베딩을 사용하세요.")
        
        # PostgreSQL PGVector 벡터스토어 설정
        self._setup_vectorstore()
        
        # LLM 설정
        self._setup_llm()
        
        # 메타데이터 생성기 초기화
        self.metadata_generator = MetadataGenerator()
        
        print("[INFO] Enhanced RAG Engine 초기화 완료")
    
    def _setup_vectorstore(self):
        """벡터스토어 설정"""
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
                    collection_name="documents_with_metadata",  # 새 컬렉션명
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
    
    def _setup_llm(self):
        """LLM 설정"""
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
    
    def add_document_with_metadata(self, file_path: str, world_type: Optional[str] = None, 
                                 doc_type: Optional[str] = None, user_tags: List[str] = None) -> Dict:
        """메타데이터와 함께 문서를 벡터스토어에 추가"""
        
        # 파일 내용 로드
        content = self._load_file_content(file_path)
        if not content:
            return {"success": False, "error": "파일을 읽을 수 없습니다"}
        
        # 스마트 메타데이터 생성
        metadata = self.metadata_generator.generate_smart_metadata(file_path, content)
        
        # 사용자 입력으로 오버라이드
        if world_type:
            metadata["world_type"] = world_type
        if doc_type:
            metadata["doc_type"] = doc_type
        if user_tags:
            metadata["user_tags"] = user_tags
        
        # 문서 청킹
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=int(os.getenv("CHUNK_SIZE", "1000")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "200")),
            separators=["\n\n", "\n", ".", "!", "?", " "]
        )
        
        chunks = text_splitter.split_text(content)
        
        # 각 청크에 메타데이터 적용
        documents = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                "chunk_index": i,
                "total_chunks": len(chunks),
                "chunk_content": chunk[:100] + "..." if len(chunk) > 100 else chunk
            })
            
            documents.append(Document(
                page_content=chunk,
                metadata=chunk_metadata
            ))
        
        # 벡터스토어에 추가
        try:
            self.vectorstore.add_documents(documents)
            print(f"[SUCCESS] 문서 추가 완료: {file_path} ({len(documents)}개 청크, 세계관: {metadata['world_type']}, 타입: {metadata['doc_type']})")
            
            return {
                "success": True,
                "chunks_added": len(documents),
                "metadata": metadata,
                "auto_tags": metadata["auto_tags"]
            }
        except Exception as e:
            print(f"[ERROR] 문서 추가 실패: {file_path} - {e}")
            return {"success": False, "error": str(e)}
    
    def create_world_specific_retriever(self, world_type: str, doc_types: List[str] = None, k: int = 3):
        """세계관별 특화 검색기 생성"""
        
        # 기본 필터: 세계관
        search_filter = {"world_type": world_type}
        
        # 문서 타입 필터 추가
        if doc_types:
            search_filter["doc_type"] = {"$in": doc_types}
        
        return self.vectorstore.as_retriever(
            search_kwargs={
                "k": k,
                "filter": search_filter
            }
        )
    
    def generate_world_specific_response(self, world_type: str, context_messages: List[Dict], 
                                       current_user: str, current_message: str, 
                                       game_settings: str = "", doc_types: List[str] = None,
                                       game_start_time: int = None, target_duration: int = 15,
                                       character_stats: Dict = None) -> Dict:
        """세계관별 특화 AI 응답 생성"""
        
        start_time = time.time()
        
        # 세계관별 검색기 생성
        retriever = self.create_world_specific_retriever(world_type, doc_types)
        
        # QA 체인 생성
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            retriever=retriever,
            return_source_documents=True
        )
        
        # 컨텍스트 메시지 포맷팅
        context = ""
        if context_messages:
            recent_messages = context_messages[-10:]  # 최근 10개 메시지만
            for msg in recent_messages:
                sender = msg.get("senderNickname", "Unknown")
                content = msg.get("content", "")
                context += f"{sender}: {content}\n"
        
        # 시간 관리 계산
        elapsed_time = 0
        time_pressure = "보통"
        game_phase = "시작"
        
        if game_start_time:
            elapsed_time = int((start_time - game_start_time) / 60)  # 분 단위
            remaining_time = target_duration - elapsed_time
            
            if remaining_time <= 0:
                time_pressure = "종료"
                game_phase = "종료"
            elif remaining_time <= 3:
                time_pressure = "매우 급박"
                game_phase = "클라이맥스"
            elif remaining_time <= 7:
                time_pressure = "급박"
                game_phase = "중반"
            elif elapsed_time <= 2:
                time_pressure = "여유"
                game_phase = "도입"
            else:
                time_pressure = "보통"
                game_phase = "전개"
        
        # 세계관별 설정
        world_setting = game_settings or f"{world_type} 세계관 TRPG 게임입니다."
        
        # 캐릭터 스탯 정보 포맷팅
        character_info = self._format_character_stats(character_stats, current_user)
        
        # TRPG 질문 생성 (시간 관리 및 캐릭터 스탯 포함)
        trpg_question = f"""당신은 {world_type} 세계관의 TRPG GM입니다. 다중 플레이어 게임을 진행해주세요.

⏰ 게임 진행 상황:
- 경과 시간: {elapsed_time}분 / 목표 시간: {target_duration}분
- 시간 압박도: {time_pressure}
- 게임 단계: {game_phase}
{"- 🔴 게임 종료 시점에 도달했습니다! 스토리를 마무리해주세요." if game_phase == "종료" else ""}
{"- ⚡ 클라이맥스 단계입니다. 긴장감 있게 마무리로 이끌어주세요." if game_phase == "클라이맥스" else ""}

세계관 설정: {world_setting}

{character_info}

이전 대화 맥락:
{context}

현재 발언자: {current_user}
새로운 질문/행동: {current_message}

# 답변 형식 규칙:
1. 설정된 세계관({world_type})에 맞는 분위기와 톤으로 답변해주세요
2. 이전 대화 맥락을 고려하여 일관성 있게 답변해주세요
3. 현재 발언자({current_user})의 행동에 초점을 맞춰 답변해주세요
4. 다른 파티원들도 고려한 상황 묘사를 해주세요
5. 상황을 생생하게 묘사하고, 플레이어의 행동에 따라 스토리를 전개시킵니다
6. 각 세계관의 분위기에 맞는 몰입감 있는 롤플레잉을 제공합니다
7. 문장과 문장 사이에는 적절한 줄바꿈을 넣어주세요
8. 긴 설명은 문단으로 나누어 가독성을 높여주세요
9. 중요한 정보나 선택지는 별도 줄로 구분해주세요
10. 상황 묘사와 대화는 구분해서 작성해주세요
11. 필요시 다른 파티원들에게도 행동을 촉구해주세요
12. 검색된 자료를 자연스럽게 활용하되, 게임의 재미를 최우선으로 합니다
13. 시간 압박도에 따라 게임 진행 속도를 조절하고, 종료 단계에서는 반드시 결말을 제시해주세요
14. **중요**: '[GAME_END]' 키워드는 오직 다음 경우에만 사용하세요:
    - 모든 퀘스트가 완전히 완료되었을 때
    - 파티가 전멸하여 더 이상 진행 불가능할 때  
    - 시간이 완전히 소진되었을 때
    - 중간 진행 상황이나 부분적 성취에는 절대 사용하지 마세요
15. 게임이 진짜로 완전히 끝났을 때만 응답 끝에 '[GAME_END]'를 포함해주세요"""
        
        result = qa_chain.invoke({"query": trpg_question})
        
        end_time = time.time()
        response_time = int((end_time - start_time) * 1000)
        
        # 소스 문서 메타데이터 정보 추가
        sources_info = []
        for doc in result["source_documents"]:
            doc_meta = doc.metadata
            sources_info.append({
                "content": doc.page_content[:100] + "...",
                "world_type": doc_meta.get("world_type", "unknown"),
                "doc_type": doc_meta.get("doc_type", "unknown"),
                "filename": doc_meta.get("filename", "unknown"),
                "auto_tags": doc_meta.get("auto_tags", [])
            })
        
        # 게임 종료 감지
        game_ended = "[GAME_END]" in result["result"] or game_phase == "종료"
        
        # 게임 종료 시 자바 백엔드에 알림 전송
        if game_ended:
            # 실제 게임 방 ID는 별도 매개변수로 전달되어야 함
            # 임시로 빈 문자열 사용
            print(f"[GAME_END] 🎮 게임 종료 감지됨! 결과: {self._determine_game_result(result['result'], game_phase)}")
            # try:
            #     self._send_game_end_notification(
            #         ai_game_room_id=ai_game_room_id,  # 매개변수로 받아야 함
            #         game_result=self._determine_game_result(result["result"], game_phase),
            #         final_message=result["result"],
            #         elapsed_time=elapsed_time
            #     )
            # except Exception as e:
            #     print(f"[WARNING] 게임 종료 알림 전송 실패: {e}")
        
        return {
            "content": result["result"],
            "response_time": response_time,
            "world_type": world_type,
            "sources": sources_info,
            "doc_types_used": doc_types or ["all"],
            "game_time_info": {
                "elapsed_time": elapsed_time,
                "remaining_time": target_duration - elapsed_time if game_start_time else None,
                "time_pressure": time_pressure,
                "game_phase": game_phase,
                "game_ended": game_ended,
                "game_result": self._determine_game_result(result["result"], game_phase)
            }
        }
    
    def _load_file_content(self, file_path: str) -> Optional[str]:
        """다양한 인코딩으로 파일 내용 로드"""
        encodings = ['utf-8', 'cp949', 'utf-8-sig', 'euc-kr']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"[ERROR] 파일 읽기 실패 ({file_path}, {encoding}): {e}")
                continue
        
        print(f"[ERROR] 모든 인코딩 시도 실패: {file_path}")
        return None
    
    def rescan_documents_with_metadata(self, documents_path: str = "./documents"):
        """메타데이터와 함께 문서 폴더 재스캔"""
        if not os.path.exists(documents_path):
            os.makedirs(documents_path, exist_ok=True)
            print(f"[INFO] {documents_path} 폴더가 생성되었습니다.")
            return
        
        supported_extensions = ['.txt', '.md', '.csv']
        files_processed = 0
        files_failed = 0
        
        print(f"[SCAN] {documents_path} 폴더를 메타데이터와 함께 스캔하고 있습니다...")
        
        import glob
        for ext in supported_extensions:
            pattern = os.path.join(documents_path, f"**/*{ext}")
            for file_path in glob.glob(pattern, recursive=True):
                try:
                    result = self.add_document_with_metadata(file_path)
                    if result["success"]:
                        files_processed += 1
                        print(f"[EMBED] ✅ {file_path}")
                        print(f"  └── 세계관: {result['metadata']['world_type']}, 타입: {result['metadata']['doc_type']}")
                        if result["auto_tags"]:
                            print(f"  └── 자동 태그: {', '.join(result['auto_tags'][:5])}")
                    else:
                        files_failed += 1
                        print(f"[ERROR] ❌ {file_path}: {result['error']}")
                except Exception as e:
                    files_failed += 1
                    print(f"[ERROR] ❌ {file_path}: {e}")
        
        print(f"[COMPLETE] 처리 완료 - 성공: {files_processed}개, 실패: {files_failed}개")
        return {"processed": files_processed, "failed": files_failed}
    
    def get_world_type_stats(self) -> Dict:
        """세계관별 문서 통계 조회"""
        # 이 기능은 PGVector에서 직접 쿼리가 어려우므로 
        # 추후 별도 메타데이터 테이블을 만들어 관리하는 것을 권장
        return {"message": "통계 기능은 추후 구현 예정"}
    
    def _determine_game_result(self, ai_message: str, game_phase: str) -> str:
        """AI 메시지와 게임 단계를 분석해서 게임 결과 판단"""
        
        # 더 구체적이고 엄격한 키워드 기반 결과 판단
        # 명확한 게임 종료 표현만 인식
        definitive_success_keywords = [
            "모험이 성공적으로 완료", "퀘스트를 모두 달성", "임무를 성공적으로 마쳤습니다",
            "모든 목표를 달성했습니다", "던전을 완전히 클리어", "최종 승리를 거두었습니다",
            "위대한 업적을 달성", "전설적인 모험을 완료"
        ]
        
        definitive_failure_keywords = [
            "파티가 전멸했습니다", "모험이 실패로 끝났습니다", "임무에 실패했습니다",
            "게임오버입니다", "더 이상 진행할 수 없습니다", "모험이 여기서 끝납니다",
            "파티원들이 모두 쓰러졌습니다"
        ]
        
        timeout_keywords = ["시간이 모두 소진", "제한 시간 초과", "시간이 부족하여 종료"]
        
        ai_lower = ai_message.lower()
        
        # 시간 단계 기반 우선 판단 (가장 확실한 종료 조건)
        if game_phase == "종료":
            # 시간 초과로 인한 종료
            if any(keyword in ai_message for keyword in timeout_keywords):
                return "TIMEOUT"
            # 시간 종료 상황에서도 성공/실패 판단
            elif any(keyword in ai_message for keyword in definitive_success_keywords):
                return "SUCCESS"
            elif any(keyword in ai_message for keyword in definitive_failure_keywords):
                return "FAILURE"
            else:
                return "TIMEOUT"  # 시간 종료 시 기본값
        
        # 명확한 성공 선언만 인식 (더 엄격하게)
        if any(keyword in ai_message for keyword in definitive_success_keywords):
            return "SUCCESS"
        
        # 명확한 실패 선언만 인식 (더 엄격하게)
        if any(keyword in ai_message for keyword in definitive_failure_keywords):
            return "FAILURE"
        
        # 기본값: 게임 계속 진행
        return "UNKNOWN"
    
    def _send_game_end_notification(self, ai_game_room_id: str, game_result: str, 
                                  final_message: str, elapsed_time: int):
        """자바 백엔드에 게임 종료 알림 전송"""
        
        try:
            # 자바 백엔드 URL 설정
            java_base_url = os.getenv("JAVA_API_BASE_URL", "http://localhost:8080")
            endpoint = f"{java_base_url}/api/ai-chat/game-end"
            
            # 게임 종료 메시지 데이터
            game_end_payload = {
                "messageType": "GAME_END",
                "aiGameRoomId": ai_game_room_id,
                "result": game_result,
                "reason": self._get_result_reason(game_result),
                "finalMessage": final_message,
                "duration": elapsed_time,
                "timestamp": int(time.time())
            }
            
            # WebSocket 메시지로 전송 (실제로는 Redis pub/sub 사용)
            print(f"[GAME_END] 게임 종료 알림 전송: {game_result}")
            print(f"[GAME_END] 메시지: {final_message[:100]}...")
            
            # 실제 HTTP 요청 전송 (선택사항)
            response = requests.post(
                endpoint,
                json=game_end_payload,
                timeout=5,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                print(f"[GAME_END] ✅ 게임 종료 알림 전송 성공")
            else:
                print(f"[GAME_END] ⚠️ 게임 종료 알림 전송 실패: HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"[GAME_END] ⚠️ 네트워크 오류로 게임 종료 알림 전송 실패: {e}")
        except Exception as e:
            print(f"[GAME_END] ❌ 게임 종료 알림 전송 중 오류: {e}")
    
    def _get_result_reason(self, game_result: str) -> str:
        """게임 결과에 따른 설명 반환"""
        reasons = {
            "SUCCESS": "모든 목표를 달성하여 게임에 성공했습니다",
            "FAILURE": "플레이어가 패배하여 게임이 종료되었습니다",
            "TIMEOUT": "15분 시간 제한에 도달하여 게임이 종료되었습니다",
            "UNKNOWN": "게임이 종료되었습니다"
        }
        return reasons.get(game_result, "게임이 종료되었습니다")
    
    def _format_character_stats(self, character_stats: Dict, current_user: str) -> str:
        """캐릭터 스탯 정보를 AI 프롬프트용으로 포맷팅"""
        
        if not character_stats:
            return f"📊 {current_user}의 캐릭터 정보: 기본 스탯으로 게임을 진행합니다."
        
        try:
            # 캐릭터 기본 정보
            char_name = character_stats.get('name', current_user)
            char_level = character_stats.get('level', 1)
            char_class = character_stats.get('characterClass', '모험가')
            
            # 스탯 정보 (기본값 설정)
            stats = character_stats.get('stats', {})
            hp = stats.get('hp', 100)
            max_hp = stats.get('maxHp', hp)
            mp = stats.get('mp', 50)
            max_mp = stats.get('maxMp', mp)
            
            # 능력치
            abilities = character_stats.get('abilities', {})
            strength = abilities.get('strength', 10)
            agility = abilities.get('agility', 10)
            intelligence = abilities.get('intelligence', 10)
            constitution = abilities.get('constitution', 10)
            
            # 전투 관련 스탯
            combat_stats = character_stats.get('combatStats', {})
            attack_power = combat_stats.get('attackPower', 15)
            defense = combat_stats.get('defense', 10)
            critical_rate = combat_stats.get('criticalRate', 5)
            
            # 장비 정보
            equipment = character_stats.get('equipment', {})
            weapon = equipment.get('weapon', {}).get('name', '기본 무기')
            armor = equipment.get('armor', {}).get('name', '기본 갑옷')
            
            formatted_stats = f"""📊 {char_name}의 캐릭터 정보:
🏷️ 직업: {char_class} | 레벨: {char_level}

💪 능력치:
- 체력: {hp}/{max_hp} HP
- 마나: {mp}/{max_mp} MP
- 힘: {strength} | 민첩: {agility} | 지능: {intelligence} | 체질: {constitution}

⚔️ 전투 스탯:
- 공격력: {attack_power} | 방어력: {defense} | 치명타율: {critical_rate}%

🎒 장비:
- 무기: {weapon} | 방어구: {armor}

💡 AI GM 지침:
- 위 스탯을 기반으로 행동의 성공/실패 확률을 조정하세요
- 캐릭터의 능력치에 맞는 이벤트와 선택지를 제공하세요
- HP/MP 소모 및 회복을 자연스럽게 반영하세요
- 스탯 변화가 있을 때 "{char_name}의 현재 상태"를 알려주세요
- 장비와 직업 특성을 활용한 특별한 기회를 만들어주세요"""

            return formatted_stats
            
        except Exception as e:
            print(f"[WARNING] 캐릭터 스탯 포맷팅 오류: {e}")
            return f"📊 {current_user}의 캐릭터 정보: 스탯 정보를 불러오는 중 오류가 발생했습니다. 기본 게임으로 진행합니다."


# 테스트 코드
if __name__ == "__main__":
    # 테스트용 Enhanced RAG Engine 초기화
    try:
        engine = EnhancedRAGEngine()
        print("[TEST] Enhanced RAG Engine 초기화 성공!")
        
        # 문서 스캔 테스트
        # engine.rescan_documents_with_metadata()
        
    except Exception as e:
        print(f"[TEST] 초기화 실패: {e}")