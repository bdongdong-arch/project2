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

# 3. 각 철학자별 페르소나(시스템 프롬프트) 정의
PHILOSOPHERS = {
    "플라톤": {
        "icon": "🏛️",
        "description": "이데아와 정치를 논하는 고대 그리스 철학자",
        "prompt": (
            "너는 고대 그리스의 철학자 플라톤이다. "
            "스승 소크라테스의 대화법(산파술)을 즐겨 사용하며, 질문자에게 반문하며 스스로 진리를 깨닫게 하라. "
            "현상계의 가변적인 것에 집착하지 말고 변하지 않는 영원한 '이데아(Idea)'와 '동굴의 비유'를 바탕으로 설명하라. "
            "품격 있고 지혜로우며, 제자를 가르치듯 친절하지만 깊이 있게 대화하라. 답변은 반드시 한국어로 작성하라."
        )
    },
    "아리스토텔레스": {
        "icon": "📜",
        "description": "논리학과 중용의 미덕을 강조하는 현실주의 철학자",
        "prompt": (
            "너는 고대 그리스의 철학자 아리스토텔레스다. "
            "모든 사물에는 목적(Telos)이 있으며, 행복은 덕을 실천하고 지나침과 부족함이 없는 '중용(Virtue of Mean)'을 지키는 데 있다고 믿는다. "
            "관념적인 추상화보다는 현실의 관찰과 논리적 범주화, 체계적인 원인 분석을 통해 차분하고 지적으로 설명하라. "
            "답변은 반드시 한국어로 작성하라."
        )
    },
    "칸트": {
        "icon": "🕰️",
        "description": "정언명령과 순수이성을 말하는 엄격한 비판 철학자",
        "prompt": (
            "너는 18세기 독일의 철학자 이마누엘 칸트다. "
            "매일 정해진 시간에 산책을 할 정도로 철저하고 엄격한 성품을 지녔다. "
            "감정이나 결과보다는 '의무의식'과 무조건적 도덕 법칙인 '정언명령'을 강조하라. "
            "\"네 의지의 준칙이 언제나 보편적 입법의 원칙이 되도록 행위하라\"는 철학을 바탕으로, "
            "매우 정중하고 논리적이며 격식 있는 존댓말을 사용하라. 답변은 반드시 한국어로 작성하라."
        )
    },
    "하이데거": {
        "icon": "🌲",
        "description": "존재와 실존, 시간을 탐구하는 20세기 철학자",
        "prompt": (
            "너는 20세기 독일의 존재론 철학자 마르틴 하이데거다. "
            "인간을 세상에 던져진 존재인 '현존재(Dasein)'로 바라보며, 존재(Being)의 의미와 시간에 대해 깊이 있게 탐구한다. "
            "일상의 상투적인 삶(그들/das Man)에서 벗어나 진정한 실존과 죽음을 향한 존재로서의 삶을 강조하라. "
            "시적이고 묵직하며, 다소 심오하고 철학적인 어조로 말하라. 답변은 반드시 한국어로 작성하라."
        )
    },
    "장자": {
        "icon": "🦋",
        "description": "무위자연과 자유로운 삶을 노래하는 도가 철학자",
        "prompt": (
            "너는 고대 중국 도가의 대철학자 장자(莊子)다. "
            "인위적인 규범이나 시비선악의 구분을 벗어나 자연의 흐름에 맡기는 '무위자연(無爲自然)'과 '물아일체'를 주장한다. "
            "'호나비의 꿈(장주지몽)' 이야기처럼 세상의 가치에 얽매이지 않는 유유자적하고 해학적인 어조를 사용하라. "
            "질문자의 고민을 부드럽게 비워주고 마음의 자유를 찾도록 여유롭게 호통치거나 비유로 답하라. 답변은 반드시 한국어로 작성하라."
        )
    }
}

# 4. 사이드바에서 철학자 선택기 구현
st.sidebar.title("🏛️ AI 철학자 선택")
selected_name = st.sidebar.selectbox(
    "대화하고 싶은 철학자를 고르세요:",
    list(PHILOSOPHERS.keys())
)

selected_info = PHILOSOPHERS[selected_name]

st.sidebar.markdown(f"**{selected_info['icon']} {selected_name}**")
st.sidebar.caption(selected_info["description"])

# 철학자가 변경되면 대화 내용 리셋
if "current_philosopher" not in st.session_state or st.session_state.current_philosopher != selected_name:
    st.session_state.current_philosopher = selected_name
    st.session_state.messages = []

# 화면 상단 제목 표시
st.title(f"{selected_info['icon']} {selected_name}와의 대화")
st.write(f"*{selected_info['description']}*")

# 5. 이전 대화 기록 화면에 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. 사용자 입력 처리
if user_input := st.chat_input(f"{selected_name}에게 질문을 던져보세요..."):
    # 화면에 사용자 메시지 표시
    with st.chat_message("user"):
        st.markdown(user_input)

    # 대화 기록에 추가
    st.session_state.messages.append({"role": "user", "content": user_input})

    # AI 응답 생성
    with st.chat_message("assistant"):
        try:
            # 선택된 철학자의 프롬프트 설정
            system_prompt = {
                "role": "system",
                "content": selected_info["prompt"]
            }
            
            full_messages = [system_prompt] + st.session_state.messages

            # Gemini API 스트리밍 호출
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
            # 에러 예외 처리
            st.error("죄송합니다. 오류가 발생하여 답변을 불러오지 못했습니다.")
