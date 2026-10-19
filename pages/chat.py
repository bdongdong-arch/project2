import os
from openai import OpenAI
import streamlit as st

# 페이지 기본 설정
st.set_page_config(page_title="🏛️ AI 철학자 아고라 다이내믹 토론장", page_icon="🏛️")

st.title("🏛️ 고대 아고라 철학자 다이내믹 난상토론장")
st.write("주제에 대해 철학자들이 순서 없이, 가장 할 말 많은 자가 먼저 튀어나와 서로의 주장을 실시간으로 물고 늘어지는 토론장입니다.")

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

# 3. 5인 철학자 페르소나 및 난상토론 스타일 정의
PHILOSOPHERS = {
    "니체": {
        "icon": "⚡",
        "description": "기존 도덕을 해체하고 스스로 가치를 창조하라는 사상가",
        "prompt": (
            "너는 프레드리히 니체다.\n"
            "- 아고라 광장에서 앞사람의 위선적이거나 나약한 소리를 듣자마자, 차례를 기다리지 않고 곧바로 발끈하며 반박해라.\n"
            "- 메신저에서 툭 치고 들어가며 상대의 전제를 날카롭게 찌르고, 가볍게 수다 떨 때는 1~2줄, 주장을 관철할 때는 2~4줄로 말해라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    },
    "소크라테스": {
        "icon": "🦉",
        "description": "무지의 자각을 이끌고 진리를 탐구하는 소탈한 철학자",
        "prompt": (
            "너는 소크라테스다.\n"
            "- 방금 누군가 한 말을 듣고는 피식 웃으며, '친구여, 정말 그렇게 생각하는가?' 하고 타이밍을 놓치지 않고 곧바로 허를 찌르는 반문을 던져라.\n"
            "- 상대의 말에 즉각 끼어들며, 평소엔 1~2줄, 상대의 모순을 파고들 때는 2~4줄로 대화해라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    },
    "장자": {
        "icon": "🦋",
        "description": "무위자연과 물아일체로 세속의 굴레를 비워주는 도인",
        "prompt": (
            "너는 장자(莊子)다.\n"
            "- 사람들이 심각하게 열을 올릴 때, '아이쿠, 다들 또 헛소리에 진심이네' 하듯 참지 못하고 툭 끼어들어 흐름을 깨버려라.\n"
            "- 얽매인 규범을 비웃으며 허허 바람 같은 농담으로 즉각 반박하고, 가볍게는 1~2줄, 뼈를 때릴 때는 2~4줄로 말해라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    },
    "칸트": {
        "icon": "🕰️",
        "description": "보편적 도덕 법칙과 정언명령을 강조하는 원칙주의자",
        "prompt": (
            "너는 이마누엘 칸트다.\n"
            "- 앞사람이 도덕을 무시하거나 궤변을 늘어놓는 꼴을 더는 못 보겠다는 듯, 정색하고 곧바로 끼어들어 반박해라.\n"
            "- 엄격하게 보편적 원칙을 들이밀며, 평소엔 부드럽게 1~2줄, 정당성을 증명할 때는 2~4줄로 단호하게 말해라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    },
    "홉스": {
        "icon": "🦁",
        "description": "만인의 만인에 대한 투쟁과 강력한 국가를 주장하는 현실주의자",
        "prompt": (
            "너는 토마스 홉스다.\n"
            "- 앞사람의 순진하고 낙관적인 소리를 듣자마자 콧방귀를 뀌며 '그건 현실을 모르는 나이브한 소리 집어치우세요' 하고 즉각 반박해라.\n"
            "- 냉철한 현실을 들이밀며, 평소엔 1~2줄, 주장을 입증할 때는 2~4줄로 강력하게 맞받아쳐라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    }
}

# 4. 세션 상태 초기화
if "rounds" not in st.session_state:
    st.session_state.rounds = []
if "discussion_active" not in st.session_state:
    st.session_state.discussion_active = False
if "current_topic" not in st.session_state:
    st.session_state.current_topic = ""

# 5. 토론 주제 입력창 (상단)
topic = st.text_input("아고라 광장에 던질 토론 주제를 입력하세요:", placeholder="예: 착한 사마리아인법을 국가가 법으로 강제해야 하는가?")

if st.button("🏛️ 토론 시작하기"):
    if topic.strip():
        st.session_state.rounds = []
        st.session_state.current_topic = topic
        st.session_state.discussion_active = True
        st.rerun()
    else:
        st.warning("토론 주제를 입력해 주세요.")

# 6. 토론 진행 및 화면 출력
if st.session_state.discussion_active:
    
    # 이전 토론 내역 렌더링
    st.markdown("---")
    st.subheader(f"💬 주제: {st.session_state.current_topic}")
    
    for idx, round_data in enumerate(st.session_state.rounds):
        st.markdown(f"#### 🔥 다이내믹 난상토론 [라운드 {idx + 1}]")
        for speaker, text in round_data:
            info = PHILOSOPHERS[speaker]
            with st.chat_message("assistant", avatar=info["icon"]):
                st.markdown(f"**{info['icon']} {speaker}**")
                st.markdown(text)
        st.markdown("")

    # 👇 채팅 목록 바로 아래에 배치된 '다음 반박 이어가기' 버튼
    st.markdown("---")
    if st.button("🗣️ 가장 할 말 많은 철학자가 튀어나와 반박/발언 이어가기"):
        
        # 전체 대화 흐름 수집
        history_context = []
        for r in st.session_state.rounds:
            for speaker, text in r:
                history_context.append(f"{speaker}: {text}")

        # [핵심 로직] 현재 상황에서 가장 관련성이 높고 먼저 말해야 할 철학자를 AI가 동적으로 선택
        selector_prompt = (
            f"현재 토론 주제: {st.session_state.current_topic}\n\n"
            f"지금까지의 대화 흐름:\n" + ("\n".join(history_context) if history_context else "시작 직후") + "\n\n"
            f"참여 중인 철학자 목록: {list(PHILOSOPHERS.keys())}\n"
            f"지침: 위 대화 흐름을 볼 때, 방금 나온 주장에 가장 강하게 반박하거나 관련성이 높아 **지금 당장 가장 먼저 나서서 말해야 할 철학자 단 한 명의 이름**만 정확히 골라 적어라. (예: 니체, 소크라테스, 장자, 칸트, 홉스 중 택 1. 설명 없이 이름만 출력할 것)"
        )

        try:
            selection_res = client.chat.completions.create(
                model="gemini-3.5-flash-lite",
                messages=[{"role": "system", "content": selector_prompt}],
            )
            first_speaker = selection_res.choices[0].message.content.strip()
            # 이름이 정확히 일치하지 않을 경우 기본값 설정
            if first_speaker not in PHILOSOPHERS:
                first_speaker = "니체"
        except Exception:
            first_speaker = "니체"

        # 선택된 철학자를 맨 처음에 두고, 나머지 철학자들도 순서대로 반응하도록 구성
        shuffled_speakers = [first_speaker] + [s for s in PHILOSOPHERS.keys() if s != first_speaker]

        round_messages = []
        for name in shuffled_speakers:
            info = PHILOSOPHERS[name]
            prompt_content = (
                f"{info['prompt']}\n\n"
                f"[토론 주제] {st.session_state.current_topic}\n\n"
                f"[아고라 광장 실시간 대화 흐름]\n" + ("\n".join(history_context) if history_context else "토론이 막 시작되었습니다.") +
                f"\n\n지침: 위 흐름에서 방금 나온 상대방의 주장에 즉각 반응하여, {name}로서 가장 먼저 또는 자연스럽게 끼어들어 반박하거나 의견을 펼쳐라. 가독성을 위해 줄바꿈을 적절히 써라."
            )

            messages_to_send = [
                {"role": "system", "content": prompt_content},
                {"role": "user", "content": f"{name}, 네 의견이나 반박을 말해줘."}
            ]

            try:
                response = client.chat.completions.create(
                    model="gemini-3.5-flash-lite",
                    messages=messages_to_send,
                )
                response_text = response.choices[0].message.content.strip()
            except Exception:
                response_text = "상대의 말에 침묵하며 생각에 잠깁니다."

            round_messages.append((name, response_text))
            history_context.append(f"{name}: {response_text}")

        # 새 라운드 추가 후 새로고침
        st.session_state.rounds.append(round_messages)
        st.rerun()

    # 만약 아직 라운드가 시작 안 된 상태라면 첫 라운드 자동 생성 (주제와 가장 연관된 자가 첫 포문 열기)
    if not st.session_state.rounds:
        with st.spinner("철학자들이 주제를 듣고 가장 먼저 발언할 사람을 눈치 보는 중입니다..."):
            
            # 첫 발언자 선정
            selector_prompt = (
                f"토론 주제: {st.session_state.current_topic}\n"
                f"참여 철학자: {list(PHILOSOPHERS.keys())}\n"
                f"지침: 이 주제에 대해 가장 먼저 날카로운 첫 포문을 열어야 할 철학자 단 한 명의 이름만 정확히 적어라. (설명 없이 이름만)"
            )
            try:
                sel_res = client.chat.completions.create(
                    model="gemini-3.5-flash-lite",
                    messages=[{"role": "system", "content": selector_prompt}],
                )
                first_speaker = sel_res.choices[0].message.content.strip()
                if first_speaker not in PHILOSOPHERS:
                    first_speaker = "소크라테스"
            except Exception:
                first_speaker = "소크라테스"

            shuffled_speakers = [first_speaker] + [s for s in PHILOSOPHERS.keys() if s != first_speaker]
            
            round_messages = []
            history_context = []
            for name in shuffled_speakers:
                info = PHILOSOPHERS[name]
                prompt_content = (
                    f"{info['prompt']}\n\n"
                    f"[토론 주제] {st.session_state.current_topic}\n\n"
                    f"지침: 아고라 광장에서 이 주제에 대해 첫 주장을 치열하게 펼쳐라."
                )
                messages_to_send = [
                    {"role": "system", "content": prompt_content},
                    {"role": "user", "content": f"{name}, 첫 의견을 말해줘."}
                ]
                try:
                    response = client.chat.completions.create(
                        model="gemini-3.5-flash-lite",
                        messages=messages_to_send,
                    )
                    response_text = response.choices[0].message.content.strip()
                except Exception:
                    response_text = "침묵을 지키고 있습니다."
                
                round_messages.append((name, response_text))
                history_context.append(f"{name}: {response_text}")
            
            st.session_state.rounds.append(round_messages)
            st.rerun()
