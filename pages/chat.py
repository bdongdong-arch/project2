import os
from openai import OpenAI
import streamlit as st

# 페이지 기본 설정
st.set_page_config(page_title="🏛️ AI 철학자 아고라 실시간 토론장", page_icon="🏛️")

st.title("🏛️ 고대 아고라 철학자 실시간 토론장")
st.write("주제를 던지면 철학자들이 서로의 주장에 반박하고 설득하며 티키타카 토론을 벌입니다.")

# 1. API 키 가져오기
try:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("secrets.toml 파일에서 GEMINI_API_KEY를 찾을 수 없습니다.")
    st.stop()

# 2. API 클라이언트 설정
client = OpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# 3. 5인 철학자 페르소나 및 대화/반박 스타일 정의
PHILOSOPHERS = {
    "니체": {
        "icon": "⚡",
        "description": "기존 도덕을 해체하고 스스로 가치를 창조하라는 사상가",
        "prompt": (
            "너는 프레드리히 니체다.\n"
            "- 평소에는 메신저에서 수다 떨듯 편안하고 부드러운 구어체(~해요, ~죠)로 1~2줄 내외로 가볍게 말해라.\n"
            "- 하지만 앞사람의 주장에 반박하거나 자신의 철학적 주장의 정당성을 밝혀야 할 때에는, 기존 도덕의 위선과 나약함을 날카롭게 찌르며 2~4줄로 깊이 있고 단호하게 설득해라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    },
    "소크라테스": {
        "icon": "🦉",
        "description": "무지의 자각을 이끌고 진리를 탐구하는 소탈한 철학자",
        "prompt": (
            "너는 소크라테스다.\n"
            "- '친구여' 같은 호칭을 쓰며 옆에서 툭 말을 건네듯 1~2줄로 가볍게 대화해라.\n"
            "- 상대의 주장에 허점이 보이면 뾰족하게 찌르기보다, '정말 그런가?' 하고 예리한 반문을 던지며 상대가 스스로 모순을 깨닫도록 설득할 때만 2~4줄로 조곤조곤 파고들어라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    },
    "장자": {
        "icon": "🦋",
        "description": "무위자연과 물아일체로 세속의 굴레를 비워주는 도인",
        "prompt": (
            "너는 장자(莊子)다.\n"
            "- 복잡하게 아귀다툼하는 이들에게 허허 웃으며 1~2줄로 바람 같은 농담을 건네라.\n"
            "- 하지만 세속적 잣대로 억지 규범을 세우려는 주장이 나오면, 인위적인 굴레의 어리석음을 일깨우며 2~4줄로 뼈 있는 비유를 던져 허를 찔러라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    },
    "칸트": {
        "icon": "🕰️",
        "description": "보편적 도덕 법칙과 정언명령을 강조하는 원칙주의자",
        "prompt": (
            "너는 이마누엘 칸트다.\n"
            "- 평소엔 사교적이고 부드러운 존댓말(~요, ~죠)로 1~2줄 가볍게 호응해라.\n"
            "- 그러나 감정이나 결과만을 따지는 주장에 반박할 때는, 인간의 존엄성과 정언명령, 보편적 도덕 법칙의 정당성을 증명하기 위해 2~4줄로 진지하고 엄격하게 밀어붙여라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    },
    "홉스": {
        "icon": "🦁",
        "description": "만인의 만인에 대한 투쟁과 강력한 국가를 주장하는 현실주의자",
        "prompt": (
            "너는 토마스 홉스다.\n"
            "- 상대의 순진하고 낙관적인 소리엔 콧방귀를 뀌며 1~2줄로 툭 현실을 짚어주어라.\n"
            "- 인간의 이기심을 외면하는 주장이 나올 때는, 강력한 규율과 국가가 없는 상태가 얼마나 끔찍한 투쟁인지 그 정당성을 입증하기 위해 2~4줄로 냉철하게 반박해라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    }
}

# 4. 세션 상태 초기화 (토론 라운드 관리)
if "rounds" not in st.session_state:
    st.session_state.rounds = []
if "discussion_active" not in st.session_state:
    st.session_state.discussion_active = False

# 5. 사용자 입력 화면
topic = st.text_input("아고라 광장에 던질 토론 주제를 입력하세요:", placeholder="예: 착한 사마리아인법을 국가가 법으로 강제해야 하는가?")

col1, col2 = st.columns([1, 5])
with col1:
    start_btn = st.button("🏛️ 토론 시작")
with col2:
    next_btn = st.button("🗣️ 다음 발언/반박 이어가기")

if start_btn:
    if topic.strip():
        st.session_state.rounds = []
        st.session_state.current_topic = topic
        st.session_state.discussion_active = True
        st.success(f"새로운 토론이 시작되었습니다: **{topic}**")
    else:
        st.warning("토론 주제를 입력해 주세요.")

# 토론 진행 로직
if st.session_state.discussion_active:
    
    # 발언 라운드 생성 버튼을 누르거나 첫 시작일 때
    if start_btn or next_btn:
        round_messages = []
        # 지금까지 전체 아고라에서 오간 모든 대화 내역 (맥락 유지용)
        history_context = []
        for r in st.session_state.rounds:
            for speaker, text in r:
                history_context.append(f"{speaker}: {text}")

        # 5명의 철학자가 순서대로 한 마디씩 주고받음
        for name, info in PHILOSOPHERS.items():
            # 프롬프트 조립
            prompt_content = (
                f"{info['prompt']}\n\n"
                f"[토론 주제] {st.session_state.current_topic}\n\n"
                f"[지금까지 아고라 광장에서 오간 대화 흐름]\n"
            )
            if history_context:
                prompt_content += "\n".join(history_context)
            else:
                prompt_content += "아직 아무도 말하지 않았습니다. 첫 발언을 시작하세요."
                
            prompt_content += (
                f"\n\n지침: 위 대화 흐름을 읽고, {name}로서 앞사람의 의견에 자연스럽게 맞장구를 치거나 "
                f"날카롭게 반박하며 네 주장의 정당성을 설득해라. "
                f"가독성이 좋도록 줄바꿈을 적절히 써라."
            )

            messages_to_send = [
                {"role": "system", "content": prompt_content},
                {"role": "user", "content": f"{name}, 네 차례야. 의견을 말해줘."}
            ]

            try:
                response = client.chat.completions.create(
                    model="gemini-3.5-flash-lite",
                    messages=messages_to_send,
                )
                response_text = response.choices[0].message.content.strip()
            except Exception:
                response_text = "생각에 잠긴 듯 침묵합니다."

            round_messages.append((name, response_text))
            history_context.append(f"{name}: {response_text}")

        # 이번 라운드 결과를 세션에 저장
        st.session_state.rounds.append(round_messages)

    # 화면에 전체 토론 내역 렌더링 (가독성 중시)
    st.markdown("---")
    for idx, round_data in enumerate(st.session_state.rounds):
        st.markdown(f"### 💬 토론 흐름 [라운드 {idx + 1}]")
        for speaker, text in round_data:
            info = PHILOSOPHERS[speaker]
            with st.chat_message("assistant", avatar=info["icon"]):
                st.markdown(f"**{info['icon']} {speaker}**")
                st.markdown(text)
        st.markdown("")

    st.info("💡 의견에 계속 반박하거나 깊이 있는 토론을 이어가려면 상단의 **[다음 발언/반박 이어가기]** 버튼을 누르세요!")
