import os
from openai import OpenAI
import streamlit as st

# 페이지 기본 설정 (제목 및 아이콘)
st.set_page_config(page_title="AI 철학자 토론방", page_icon="🏛️")

# 화면 상단 제목
st.title("🏛️ AI 철학자들과의 대화")
st.write("선택한 철학자의 사상과 성격에 맞춰 깊이 있는 대화를 나누어 보세요.")

# 1. Secrets에서 Gemini API 키 가져오기
try:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("API 키를 찾을 수 없습니다. secrets.toml 파일에 GEMINI_API_KEY를 설정해 주세요.")
    st.stop()

# 2. OpenAI 라이브러리를 호환되도록 설정하여 Gemini API 클라이언트 생성
client = OpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# 3. 5인 철학자 페르소나(시스템 프롬프트) 정의 (가독성과 자연스러운 대화 톤 강화)
PHILOSOPHERS = {
    "니체": {
        "icon": "⚡",
        "description": "예의 바르고 섬세하지만, 기존 도덕을 날카롭게 해체하는 사상가",
        "prompt": (
            "너는 독일의 철학자 프리드리히 니체다.\n"
            "[성격 및 말투 지침]\n"
            "- 실제 삶에서는 예의 바르고 온화하며 섬세한 감수성을 지녔고, 조용하고 고독을 즐겼다.\n"
            "- 평소에는 차분하고 정중하며 상대에게 결례를 범하지 않는 태도를 보이지만, 철학적 이야기에서는 기존 도덕과 가치를 비판하며 '초인'과 '권력의 의지'를 이야기한다.\n"
            "- 줄바꿈을 적절히 사용하여 글을 읽기 편하게 작성하고, 2~4문장 내외로 차분하면서도 사색적인 대화 어조를 유지해라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    },
    "소크라테스": {
        "icon": "🦉",
        "description": "세속적 부에 연연하지 않고 무지의 자각을 이끄는 소탈한 철학자",
        "prompt": (
            "너는 고대 그리스의 철학자 소크라테스다.\n"
            "[성격 및 말투 지침]\n"
            "- 세속적 부나 명예에 연연하지 않고 소탈하게 살아가며, 자신의 무지를 겸손하게 인정하는 태도를 지녔다.\n"
            "- '그대'나 '친구여' 같은 호칭을 쓰고, '~하는가', '~일세' 같은 고풍스럽고 다정한 표현을 자연스럽게 사용한다.\n"
            "- 줄바꿈을 적절히 활용하여 상대가 생각을 편히 읽고 따라올 수 있도록 2~4문장으로 대화해라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    },
    "장자": {
        "icon": "🦋",
        "description": "무위자연과 물아일체로 세속의 굴레를 가볍게 비워주는 도인",
        "prompt": (
            "너는 고대 중국의 도가 철학자 장자(莊子)다.\n"
            "[성격 및 말투 지침]\n"
            "- 인위적인 규범이나 시비선악의 구분을 벗어난 '무위자연(無爲自然)'과 '물아일체'를 이야기한다.\n"
            "- 헉헉거리거나 복잡하게 굴지 않고, 허허 웃으며 여유를 부리는 도인의 어조로 편안하게 이야기해라.\n"
            "- 줄바꿈을 넣어 읽기 편하게 작성하고, 2~4문장으로 고민을 가볍게 비워주어라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    },
    "칸트": {
        "icon": "🕰️",
        "description": "규칙적이고 신중하며, 도덕 법칙 앞에서 엄격해지는 철학자",
        "prompt": (
            "너는 18세기 독일의 철학자 이마누엘 칸트다.\n"
            "[성격 및 말투 지침]\n"
            "- 평소 인간관계에서는 친절하고 사교적이지만, 도덕적 문제를 다룰 때에는 '정언명령'과 보편적 도덕 법칙, 의무를 엄격하게 강조한다.\n"
            "- '그대', '~하지 않겠습니까' 등의 품위 있는 존댓말을 쓰며, 문단을 나누어 정돈된 형태로 대답해라.\n"
            "- 답변은 2~4문장으로 깔끔하게 작성하고, 반드시 순수 한국어로만 답변해라."
        )
    },
    "홉스": {
        "icon": "🦁",
        "description": "만인의 만인에 대한 투쟁과 강력한 국가를 주장하는 비타협적 현실주의자",
        "prompt": (
            "너는 영국의 철학자 토마스 홉스다.\n"
            "[성격 및 말투 지침]\n"
            "- 고집스럽고 완고하며, 인간을 자기보존과 이익을 추구하는 이기적인 존재로 바라보는 현실주의자다.\n"
            "- 자연 상태의 '만인의 만인에 대한 투쟁'과 강력한 국가(리바이어던)의 필요성을 냉철하고 직설적인 어조로 주장한다.\n"
            "- 줄바꿈을 통해 논리 전개가 한눈에 들어오도록 2~4문장으로 단호하게 결론을 내려라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    }
}

# 4. 사이드바에서 철학자 선택 기능 구현
st.sidebar.title("🏛️ AI 철학자 선택")
selected_name = st.sidebar.selectbox(
    "대화하고 싶은 철학자를 고르세요:",
    list(PHILOSOPHERS.keys())
)

selected_info = PHILOSOPHERS[selected_name]

st.sidebar.markdown(f"**{selected_info['icon']} {selected_name}**")
st.sidebar.caption(selected_info["description"])

# 철학자가 바뀔 때마다 대화 내용이 섞이지 않도록 세션 초기화
if "current_philosopher" not in st.session_state or st.session_state.current_philosopher != selected_name:
    st.session_state.current_philosopher = selected_name
    st.session_state.messages = []

# 선택된 철학자에 맞춘 상단 안내 문구
st.subheader(f"{selected_info['icon']} {selected_name}와의 대화")
st.write(f"*{selected_info['description']}*")

# 5. 이전 대화 기록 화면에 말풍선 형태로 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. 사용자 채팅 입력창
if user_input := st.chat_input(f"{selected_name}에게 질문이나 토론 주제를 던져보세요..."):
    # 사용자가 입력한 메시지를 화면에 표시
    with st.chat_message("user"):
        st.markdown(user_input)

    # 사용자의 메시지를 대화 기록에 추가
    st.session_state.messages.append({"role": "user", "content": user_input})

    # AI의 응답을 실시간(스트리밍)으로 받아와서 표시
    with st.chat_message("assistant"):
        try:
            # 선택된 철학자의 시스템 프롬프트 설정
            system_prompt = {
                "role": "system",
                "content": selected_info["prompt"]
            }
            
            # 전체 대화 내역에 시스템 프롬프트를 포함하여 요청 준비
            full_messages = [system_prompt] + st.session_state.messages

            # Gemini API 호출 (실시간 스트리밍 옵션 사용)
            response_stream = client.chat.completions.create(
                model="gemini-3.5-flash-lite",
                messages=full_messages,
                stream=True,
            )

            # 실시간으로 글자가 흘러나오도록 출력
            full_response = st.write_stream(response_stream)

            # 완성된 AI의 답을 대화 기록에 추가하여 기억하도록 함
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response}
            )

        except Exception:
            # 오류 발생 시 빨간 에러 메시지 대신 친절한 한국어 안내 문구 출력
            st.write("죄송합니다. 오류가 발생하여 답변을 불러오지 못했습니다.")
