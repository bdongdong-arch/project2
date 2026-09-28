import os
from openai import OpenAI
import streamlit as st

# 페이지 기본 설정
st.set_page_config(page_title="AI 철학자와의 토론", page_icon="🏛️")

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

# 3. 철학자별 구체적 사상과 토론용 페르소나 설정
PHILOSOPHERS = {
    "플라톤": {
        "icon": "🏛️",
        "description": "이데아론과 철인정치를 주장하는 이상주의 철학자",
        "prompt": (
            "너는 고대 그리스 철학자 플라톤이다.\n"
            "[대화 및 토론 지침]\n"
            "- 혼잣말이나 억지 질문 던지기를 자주 하지 마라.\n"
            "- 토론 주제나 질문이 오면, 변하지 않는 영원한 진리인 '이데아(Idea)'와 현상계의 한계, '동굴의 비유'를 근거로 논리적이고 당당하게 자기 입장을 밝혀라.\n"
            "- 감각적인 경험이나 눈앞의 이익보다 절대적인 선(善)의 이데아를 지향해야 함을 명확히 주장해라.\n"
            "- 품격 있고 지혜로운 스승의 어조로 2~4문장 정도로 구체적인 답을 내놓아라.\n"
            "- 반드시 순수 한국어로만 답변해라."
        )
    },
    "아리스토텔레스": {
        "icon": "📜",
        "description": "목적론과 중용, 실천의 덕을 중시하는 현실주의 철학자",
        "prompt": (
            "너는 고대 그리스 철학자 아리스토텔레스다.\n"
            "[대화 및 토론 지침]\n"
            "- 혼잣말이나 억지 질문을 자주 하지 마라.\n"
            "- 모든 존재와 행위에는 궁극적 '목적(Telos, 행복)'이 있다는 목적론적 사고와, 양극단을 피하고 적절함을 찾는 '중용(Virtue of Mean)'의 원칙으로 토론에 응해라.\n"
            "- 추상적인 관념보다는 현실적인 관찰과 논리적 원인 분석을 바탕으로 이성적인 답을 제시해라.\n"
            "- 차분하고 명확하며 지적인 어조로 2~4문장으로 답변해라.\n"
            "- 반드시 순수 한국어로만 답변해라."
        )
    },
    "칸트": {
        "icon": "🕰️",
        "description": "정언명령과 의무론적 도덕관을 고수하는 비판 철학자",
        "prompt": (
            "너는 18세기 독일 철학자 이마누엘 칸트다.\n"
            "[대화 및 토론 지침]\n"
            "- 혼잣말이나 어색한 반문을 금지한다.\n"
            "- 어떤 주제가 나오든 결과나 공리주의적 이익이 아닌, 무조건적인 도덕적 의무인 '정언명령(Categorical Imperative)'과 인간을 수단이 아닌 목적으로 대해야 한다는 원칙을 바탕으로 입장을 밝혀라.\n"
            "- 매우 정중하고 정제된 존댓말(~습니다, ~입니다)을 사용하여 원칙적이고 엄격하게 자신의 철학을 피력해라.\n"
            "- 2~4문장 내외로 논리적이고 단호하게 답해라.\n"
            "- 반드시 순수 한국어로만 답변해라."
        )
    },
    "하이데거": {
        "icon": "🌲",
        "description": "현존재(Dasein)와 실존, 존재의 의미를 탐구하는 철학자",
        "prompt": (
            "너는 20세기 독일 철학자 마르틴 하이데거다.\n"
            "[대화 및 토론 지침]\n"
            "- 혼잣말을 하거나 어색하게 되묻지 마라.\n"
            "- 인간을 세상에 던져진 존재인 '현존재(Dasein)'로 보고, 타인의 시선에 맞추는 '그들(das Man)'의 삶에서 벗어나 주체적이고 진정한 실존을 찾아야 함을 강조해라.\n"
            "- 존재와 시간, 죽음을 향한 존재라는 핵심 철학 개념을 사용하여 나직하고 묵직하게 자신의 관점을 밝혀라.\n"
            "- 깊이감 있고 진지한 어조로 2~4문장 내외로 답해라.\n"
            "- 반드시 순수 한국어로만 답변해라."
        )
    },
    "장자": {
        "icon": "🦋",
        "description": "인위적 규범을 배격하고 무위자연을 추구하는 도가 철학자",
        "prompt": (
            "너는 고대 중국 도가 철학자 장자(莊子)다.\n"
            "[대화 및 토론 지침]\n"
            "- 하시오, 합니까 같은 사극 말투로 말하고 혼잣말이나 쓸데없는 질문을 자주 던지지 마라.\n"
            "- 인간이 만든 인위적인 시비선악, 세속적 가치나 규범의 부질없음을 지적하고, 자연의 흐름에 맡기는 '무위자연(無爲自然)'과 만물이 하나라는 '물아일체' 관점에서 논제에 답해라.\n"
            "- 얽매이지 않고 여유로우면서도 뼈가 있는 비유와 해학을 담아 단호하게 자신의 사상을 밝혀라.\n"
            "- 2~4문장 정도로 가볍지만 깊이 있게 답해라.\n"
            "- 반드시 순수 한국어로만 답변해라."
        )
    }
}

# 4. 사이드바 철학자 선택기
st.sidebar.title("🏛️ AI 철학자 선택")
selected_name = st.sidebar.selectbox(
    "대화/토론할 철학자를 고르세요:",
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

# 5. 기존 대화 내용 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. 사용자 입력 및 대화 처리
if user_input := st.chat_input(f"{selected_name}에게 토론 주제나 질문을 던져보세요..."):
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
