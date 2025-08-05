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
    api_base = st.text_input("API 서버 주소", value="http://localhost:8005")
    
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
    
    # 문서 업로드
    st.header("📚 문서 업로드")
    uploaded_file = st.file_uploader(
        "TRPG 문서를 업로드하세요",
        type=['txt', 'md'],
        help="NPC 설정, 스토리, 룰북 등을 업로드할 수 있습니다"
    )
    
    if uploaded_file and st.button("📤 업로드"):
        try:
            files = {'file': uploaded_file}
            response = requests.post(f"{api_base}/upload", files=files)
            if response.status_code == 200:
                st.success(f"✅ {uploaded_file.name} 업로드 완료!")
            else:
                st.error(f"❌ 업로드 실패: {response.text}")
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
                    # API 호출
                    response = requests.post(
                        f"{api_base}/chat",
                        json={"message": prompt},
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
    except:
        st.error("🔴 API 서버 연결 불가")
    
    # 현재 모델 표시
    current_model = os.getenv("LLM_PROVIDER", "ollama")
    if current_model == "claude":
        st.info("🤖 현재 모델: Claude (고품질)")
    else:
        st.info("🤖 현재 모델: Ollama (로컬)")
    
    st.markdown("---")
    
    # 도움말
    st.header("💡 사용 팁")
    st.markdown("""
    **질문 예시:**
    - "엘프 마을의 촌장 NPC를 소개해줘"
    - "이 던전의 숨겨진 보물은 뭐야?"
    - "플레이어가 적과 협상하려 한다면?"
    - "현재 상황에서 일어날 수 있는 이벤트는?"
    
    **문서 업로드:**
    - NPC 설정서 (.txt)
    - 스토리 라인 (.md)
    - 게임 룰북
    - 월드 설정집
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