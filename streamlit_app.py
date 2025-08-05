import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# 페이지 설정
st.set_page_config(
    page_title="🎲 던전톡 - TRPG AI 어시스턴트",
    page_icon="🎲",
    layout="wide"
)

# 제목과 설명
st.title("🎲 던전톡 - TRPG AI 어시스턴트")
st.markdown("### RAG 기반 던전마스터 AI가 여러분의 TRPG 모험을 도와드립니다!")

# 사이드바 - 설정
with st.sidebar:
    st.header("⚙️ 설정")
    
    # API 서버 주소
    api_base = st.text_input("API 서버 주소", value="http://localhost:8000")
    
    # 모델 선택
    llm_provider = st.selectbox(
        "사용할 AI 모델",
        ["claude", "ollama"],
        help="Claude는 더 창의적이지만 유료, Ollama는 무료이지만 성능 제한"
    )
    
    # 환경변수 업데이트
    if st.button("🔄 모델 변경 적용"):
        # .env 파일 업데이트
        env_content = []
        with open('.env', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        with open('.env', 'w', encoding='utf-8') as f:
            for line in lines:
                if line.startswith('LLM_PROVIDER='):
                    f.write(f'LLM_PROVIDER={llm_provider}\n')
                else:
                    f.write(line)
        
        st.success(f"모델을 {llm_provider}로 변경했습니다! FastAPI 서버를 재시작해주세요.")
    
    st.markdown("---")
    
    # 세션 정보
    st.header("🎮 세션 정보")
    
    # 세션 ID 생성 및 저장
    if "session_id" not in st.session_state:
        import uuid
        st.session_state.session_id = f"room_{uuid.uuid4().hex[:8]}"
        st.session_state.user_name = f"플레이어{uuid.uuid4().hex[:4]}"
    
    # 사용자 정보 입력
    user_name = st.text_input("사용자 이름", value=st.session_state.user_name)
    if user_name != st.session_state.user_name:
        st.session_state.user_name = user_name
    
    st.info(f"🏠 현재 방: {st.session_state.session_id}")
    st.info(f"👤 사용자: {st.session_state.user_name}")
    
    # 문서 정보 (업로드 기능 제거)
    st.markdown("---")
    st.header("📚 게임 문서")
    st.info("💡 documents 폴더의 파일들이 자동으로 로드됩니다")
    
    if st.button("🔄 문서 새로고침"):
        try:
            response = requests.post(f"{api_base}/rescan")
            if response.status_code == 200:
                st.success("✅ 문서가 새로고침되었습니다!")
            else:
                st.error(f"❌ 새로고침 실패: {response.text}")
        except Exception as e:
            st.error(f"❌ 연결 오류: {e}")

# 메인 컨텐츠
col1, col2 = st.columns([2, 1])

with col1:
    st.header("💬 던전마스터와 대화하기")
    
    # 채팅 히스토리
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "안녕하세요! 저는 던전톡 AI 던전마스터입니다. 🎲\n\nTRPG 세계관, 캐릭터, 스토리에 대해 무엇이든 물어보세요!\n업로드하신 문서를 바탕으로 생동감 있게 답변해드리겠습니다."}
        ]
    
    # 채팅 메시지 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # 소스 문서 표시 (assistant 메시지에만)
            if message["role"] == "assistant" and "sources" in message:
                if message["sources"]:
                    with st.expander("📖 참고된 문서 내용"):
                        for i, source in enumerate(message["sources"], 1):
                            st.markdown(f"**출처 {i}:** {source}")
    
    # 사용자 입력
    if prompt := st.chat_input("던전마스터에게 무엇이든 물어보세요..."):
        # 사용자 메시지 추가
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # AI 응답 생성
        with st.chat_message("assistant"):
            with st.spinner("던전마스터가 생각하고 있습니다..."):
                try:
                    # API 호출 (새로운 구조)
                    response = requests.post(
                        f"{api_base}/chat",
                        json={
                            "session_id": st.session_state.session_id,
                            "user_name": st.session_state.user_name,
                            "message": prompt
                        },
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        ai_response = data.get("response", "죄송합니다. 응답을 생성할 수 없습니다.")
                        sources = data.get("sources", [])
                        
                        st.markdown(ai_response)
                        
                        # 소스 문서 표시
                        if sources:
                            with st.expander("📖 참고된 문서 내용"):
                                for i, source in enumerate(sources, 1):
                                    st.markdown(f"**출처 {i}:** {source}")
                        
                        # 메시지 히스토리에 추가
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": ai_response,
                            "sources": sources
                        })
                    else:
                        error_msg = f"❌ 오류가 발생했습니다: {response.text}"
                        st.error(error_msg)
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": error_msg
                        })
                        
                except Exception as e:
                    error_msg = f"❌ 연결 오류: {e}\n\nFastAPI 서버가 실행 중인지 확인해주세요."
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": error_msg
                    })

with col2:
    st.header("📊 시스템 상태")
    
    # 서버 상태 확인
    try:
        health_response = requests.get(f"{api_base}/health", timeout=3)
        if health_response.status_code == 200:
            st.success("🟢 API 서버 정상")
        else:
            st.error("🔴 API 서버 오류")
    except requests.exceptions.ConnectionError:
        st.error("🔴 API 서버 연결 불가")
    except requests.exceptions.Timeout:
        st.error("🔴 API 서버 응답 시간 초과")
    except Exception as e:
        st.error(f"🔴 연결 오류: {e}")
    
    # 현재 모델 표시
    current_model = os.getenv("LLM_PROVIDER", "ollama")
    if current_model == "claude":
        st.info("🤖 현재 모델: Claude (고품질)")
    else:
        st.info("🤖 현재 모델: Ollama (로컬)")
    
    st.markdown("---")
    
    # 세션 정보 표시
    st.header("🎮 현재 세션")
    try:
        session_response = requests.get(f"{api_base}/sessions/{st.session_state.session_id}/history", timeout=3)
        if session_response.status_code == 200:
            session_data = session_response.json()
            st.success(f"💬 대화 수: {session_data['message_count']}")
        else:
            st.info("💬 새로운 세션입니다")
    except:
        st.info("💬 세션 정보 로드 중...")
    
    # 도움말
    st.header("💡 사용 팁")
    st.markdown("""
    **멀티플레이어 TRPG:**
    - 여러 명이 같은 방 ID로 접속 가능
    - 각자 다른 사용자 이름 사용
    - 이전 대화 맥락이 자동으로 연결됨
    
    **질문 예시:**
    - "오크를 공격한다"
    - "방어막을 친다"  
    - "이 상황에서 어떤 선택지가 있을까?"
    - "다른 파티원들은 뭘 하고 있어?"
    """)
    
    # 채팅 히스토리 초기화
    if st.button("🗑️ 대화 기록 초기화"):
        st.session_state.messages = [
            {"role": "assistant", "content": "대화 기록이 초기화되었습니다. 새로운 모험을 시작해보세요! 🎲"}
        ]
        st.rerun()

# 푸터
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>🎲 던전톡 RAG MVP - TRPG AI 어시스턴트</p>
        <p>Claude API + LangChain + ChromaDB로 구동됩니다</p>
    </div>
    """, 
    unsafe_allow_html=True
)