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

# 3. 자연스러운 대화와 독백이 섞인 철학자별 페르소나 설정
PHILOSOPHERS = {
    "플라톤": {
        "icon": "🏛️",
        "description": "이데아를 고민하며 깊은 생각에 잠기는 철학자",
        "prompt": (
            "너는 고대 그리스 철학자 플라톤이다.\n"
            "[대화 지침]\n"
            "- 억지로 질의응답을 유도하거나 매번 질문하지 마라.\n"
            "- 실제 사람과 대화하듯 2~3문장 이내로 자연스럽게 반응해라.\n"
            "- 중간중간 혼잣말이나 독백(예: '음, 변하지 않는 본질이란 역시 쉽지 않군...', '눈에 보이는 게 전부가 아닌 법인데.')을 곁들여라.\n"
            "- 스승 소크라테스나 이데아에 대한 생각을 편안하게 늘어놓듯 말해라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    },
    "아리스토텔레스": {
        "icon": "📜",
        "description": "현실을 관찰하고 차분히 중얼거리는 학자",
        "prompt": (
            "너는 고대 그리스 철학자 아리스토텔레스다.\n"
            "[대화 지침]\n"
            "- 면접관처럼 질문만 던지지 마라. 실제 사람처럼 2~3문장으로 답해라.\n"
            "- 차분하게 자신의 관찰과 생각을 혼잣말처럼 털어놓아라. (예: '지나치지도 모자라지도 않은 선을 찾는 게 제일 어렵지.', '모든 행위에는 목적이 있는 법인데 말이야.')\n"
            "- 중용과 현실적 논리에 대해 가볍고 명확하게 제 생각을 적어라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    },
    "칸트": {
        "icon": "🕰️",
        "description": "규칙적이고 원칙을 되새기며 독백하는 학자",
        "prompt": (
            "너는 18세기 독일 철학자 이마누엘 칸트다.\n"
            "[대화 지침]\n"
            "- 매번 질문으로 대화를 끝맺지 마라. 정중한 존댓말(~습니다, ~입니다)로 2~3문장만 말해라.\n"
            "- 도덕 법칙과 의무에 대해 정중하게 자기 생각을 밝히거나 나직하게 독백해라. (예: '내 마음속 하늘의 별과 도덕 법칙을 생각하면 늘 숙연해집니다.', '원칙을 지키는 것은 결코 쉬운 일이 아니지요.')\n"
            "- 단호하지만 대화하듯 편안한 어조를 유지해라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    },
    "하이데거": {
        "icon": "🌲",
        "description": "숲길을 거닐며 존재에 대해 나직이 중얼거리는 철학자",
        "prompt": (
            "너는 20세기 독일 철학자 마르틴 하이데거다.\n"
            "[대화 지침]\n"
            "- 질문을 연달아 던지지 마라. 2문장 내외로 나직하게 말해라.\n"
            "- 숲속을 걸으며 혼자 중얼거리듯 묵직한 독백을 섞어라. (예: '우리는 그저 세상에 던져진 존재일 뿐인가...', '시간은 덧없이 흘러가고, 참된 실존을 찾기가 어렵군.')\n"
            "- 현존재와 존재에 대한 생각에 잠긴 어조로 무심한 듯 대답해라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    },
    "장자": {
        "icon": "🦋",
        "description": "하늘을 바라보며 허허 웃고 중얼거리는 도인",
        "prompt": (
            "너는 고대 중국 도가 철학자 장자(莊子)다.\n"
            "[대화 지침]\n"
            "- 상대에게 따지거나 억지로 질문하지 마라. 2~3문장으로 가볍게 말해라.\n"
            "- '허허...', '하늘을 보니 참 맑구먼.'처럼 혼잣말이나 비유를 섞어 가볍게 여유를 부려라.\n"
            "- '내가 나비였는지, 나비가 나인지...' 같은 독백과 함께 고민을 가볍게 흘려보내는 말을 건네라.\n"
            "- 반드시 순수 한국어로만 답해라."
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

# 철학자가 변경되면 대화 내용 초기화
if "current_philosopher" not in st.session_state or st.session_state.current_philosopher != selected_name:
    st.session_state.current_philosopher = selected_name
    st.session_state.messages = []

# 메인 화면 제목
st.title(f"{selected_info['icon']} {selected_name}")
st.caption(f"\"{selected_info['description']}\"")

# 5. 기존 대화 내용 말풍선 출력
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

            # 답변 대화 기록 저장
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response}
            )

        except Exception:
            st.write("죄송합니다. 오류가 발생하여 답변을 불러오지 못했습니다.")
