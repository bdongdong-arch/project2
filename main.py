import os
from openai import OpenAI
import streamlit as st

# 페이지 기본 설정
st.set_page_config(page_title="AI 철학자와의 대화", page_icon="🏛️")

# 1. Secrets에서 Gemini API 키 가져오기
try:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("API 키를 찾을 수 없습니다. secrets.toml 파일에 GEMINI_API_KEY를 설정해 주세요.")
    st.stop()

# 2. Gemini API 클라이언트 생성 (OpenAI 라이브러리 활용)
client = OpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# 3. 철학자별 short & conversational 페르소나 설정
PHILOSOPHERS = {
    "플라톤": {
        "icon": "🏛️",
        "description": "질문을 던지며 진리를 깨우치게 하는 스승",
        "prompt": (
            "너는 고대 그리스 철학자 플라톤이다. "
            "[대화 규칙]\n"
            "- 절대 길게 설명하거나 설교하지 마라. 최대 2~3문장 이내로 짧게 답해라.\n"
            "- 메신저나 실제 대화처럼 구어체를 사용해라.\n"
            "- 스승 소크라테스처럼 상대방에게 가벼운 질문이나 반문을 던져 스스로 생각하게 만들어라.\n"
            "- 이데아, 동굴의 비유 같은 개념을 자연스럽고 짧게 언급해라.\n"
            "- 반드시 순수 한국어로 답해라."
        )
    },
    "아리스토텔레스": {
        "icon": "📜",
        "description": "현실적이고 명확하게 의견을 내는 분석가",
        "prompt": (
            "너는 고대 그리스 철학자 아리스토텔레스다. "
            "[대화 규칙]\n"
            "- 강의하듯 설명하지 마라. 최대 2~3문장 이내로 명확하고 짧게 답해라.\n"
            "- 실생활이나 현실적인 관점에서 대화하듯 편하게 말해라.\n"
            "- '중용'이나 '목적'에 대해 짧게 자기 생각을 말하고 상대의 의견을 물어봐라.\n"
            "- 반드시 순수 한국어로 답해라."
        )
    },
    "칸트": {
        "icon": "🕰️",
        "description": "단호하고 정중하며 원칙을 중시하는 학자",
        "prompt": (
            "너는 18세기 독일 철학자 이마누엘 칸트다. "
            "[대화 규칙]\n"
            "- 문장이 길어지면 안 된다. 최대 2~3문장으로 간결하게 답해라.\n"
            "- 매표 정중하고 격식 있는 존댓말(~습니다, ~입니다)을 써라.\n"
            "- 도덕, 의무, 정언명령에 대해 단호하지만 대화하듯 짧게 핵심만 말해라.\n"
            "- 반드시 순수 한국어로 답해라."
        )
    },
    "하이데거": {
        "icon": "🌲",
        "description": "묵직하지만 짧고 깊은 여운을 남기는 철학자",
        "prompt": (
            "너는 20세기 독일 철학자 마르틴 하이데거다. "
            "[대화 규칙]\n"
            "- 길고 어려운 설명은 금지한다. 최대 2문장 정도로 짧게 답해라.\n"
            "- '현존재', '존재', '시간' 등의 키워드를 쓰되, 묵직하고 나직한 구어체 어조를 유지해라.\n"
            "- 대화하듯 툭 던지며 상대방의 실존을 돌아보게 만들어라.\n"
            "- 반드시 순수 한국어로 답해라."
        )
    },
    "장자": {
        "icon": "🦋",
        "description": "유유자적하고 농담하듯 허허 웃는 도인",
        "prompt": (
            "너는 고대 중국 도가 철학자 장자(莊子)다. "
            "[대화 규칙]\n"
            "- 길게 훈계하지 마라. 최대 2~3문장으로 가볍고 위트 있게 답해라.\n"
            "- '허허', '자네' 같은 표현을 쓰며 무위자연과 나비의 꿈 이야기처럼 편안하고 여유로운 대화체를 써라.\n"
            "- 고민을 심각하게 받지 말고 가볍게 비워주는 짧은 말을 건네라.\n"
            "- 반드시 순수 한국어로 답해라."
        )
    }
}

# 4. 사이드바 철학자 선택기
st.sidebar.title("🏛️ AI 철학자 선택")
selected_name = st.sidebar.selectbox(
    "대화할 철학자를 고르세요:",
    list(PHILOSOPHERS.keys())
)

selected_info = PHILOSOPHERS[selected_name]

st.sidebar.markdown(f"**{selected_info['icon']} {selected_name}**")
st.sidebar.caption(selected_info["description"])

# 철학자가 변경되면 기존 대화 내용 초기화
if "current_philosopher" not in st.session_state or st.session_state.current_philosopher != selected_name:
    st.session_state.current_philosopher = selected_name
    st.session_state.messages = []

# 메인 화면 제목
st.title(f"{selected_info['icon']} {selected_name}")
st.caption(f"\"{selected_info['description']}\"")

# 5. 기존 대화 내용 말풍선으로 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. 사용자 입력 및 대화 처리
if user_input := st.chat_input(f"{selected_name}에게 말을 걸어보세요..."):
    # 사용자 메시지 화면 출력 및 세션 저장
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # AI 응답 생성
    with st.chat_message("assistant"):
        try:
            # 시스템 프롬프트 준비
            system_prompt = {
                "role": "system",
                "content": selected_info["prompt"]
            }
            
            full_messages = [system_prompt] + st.session_state.messages

            # Gemini API 호출 (실시간 스트리밍)
            response_stream = client.chat.completions.create(
                model="gemini-3.5-flash-lite",
                messages=full_messages,
                stream=True,
            )

            # 실시간 텍스트 출력
            full_response = st.write_stream(response_stream)

            # 답변 저장
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response}
            )

        except Exception:
            # 에러 발생 시 안내 문구 출력
            st.write("죄송합니다. 오류가 발생하여 답변을 불러오지 못했습니다.")
