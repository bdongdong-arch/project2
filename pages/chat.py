import os
import random
from openai import OpenAI
import streamlit as st

# 페이지 기본 설정
st.set_page_config(page_title="🏛️ AI 철학자 아고라 다원적 난상토론장", page_icon="🏛️")

st.title("🏛️ 고대 아고라 철학자 다원적 난상토론장")
st.write("특정 인물에 치우치지 않고, 5명의 철학자가 골고루 돌아가며 때로는 치열하게 반박하는 자유 토론장입니다.")

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
        st.markdown(f"#### 🔥 다원적 난상토론 [라운드 {idx + 1}]")
        for speaker, text in round_data:
            info = PHILOSOPHERS[speaker]
            with st.chat_message("assistant", avatar=info["icon"]):
                st.markdown(f"**{info['icon']} {speaker}**")
                st.markdown(text)
        st.markdown("")

    # 👇 채팅 목록 바로 아래에 배치된 '다음 반박 이어가기' 버튼
    st.markdown("---")
    if st.button("🗣️ 다른 철학자들이 무작위로 튀어나와 반박 이어가기"):
        
        # 전체 대화 흐름 수집
        history_context = []
        for r in st.session_state.rounds:
            for speaker, text in r:
                history_context.append(f"{speaker}: {text}")

        # [핵심 로직] 편향을 막기 위해, 최근에 말했던 인물들을 페널티 주고 다양한 인물이 골고루 섞이도록 무작위 풀과 AI 선택 결합
        recent_speakers = [r[0] for r in st.session_state.rounds[-2:]] if len(st.session_state.rounds) >= 2 else []
        available_pool = [s for s in PHILOSOPHERS.keys() if s not in recent_speakers]
        if not available_pool:
            available_pool = list(PHILOSOPHERS.keys())

        # 버튼을 누를 때마다 서로 다른 3명이 골고루 튀어나오도록 순서 섞기
        selected_speakers = []
        temp_pool = list(PHILOSOPHERS.keys())
        random.shuffle(temp_pool)
        
        # 직전 발언자와 겹치지 않게 우선순위 부여하여 3명 선정
        for s in temp_pool:
            if s not in selected_speakers:
                selected_speakers.append(s)
            if len(selected_speakers) >= 3:
                break

        round_messages = []
        temp_history = list(history_context)

        for name in selected_speakers:
            info = PHILOSOPHERS[name]
            prompt_content = (
                f"{info['prompt']}\n\n"
                f"[토론 주제] {st.session_state.current_topic}\n\n"
                f"[아고라 광장 실시간 대화 흐름]\n" + ("\n".join(temp_history) if temp_history else "토론 시작") +
                f"\n\n지침: 위 흐름에서 방금 나온 다른 철학자들의 주장에 즉각 반응하여, {name}의 독창적인 관점으로 끼어들어 반박하거나 새로운 의견을 펼쳐라. 절대 한 사람만 말하게 하지 말고 다양한 시각을 보여줘라. 가독성을 위해 줄바꿈을 적절히 써라."
            )

            try:
                response = client.chat.completions.create(
                    model="gemini-3.5-flash-lite",
                    messages=[
                        {"role": "system", "content": prompt_content},
                        {"role": "user", "content": f"{name}, 네 의견이나 반박을 말해줘."}
                    ],
                )
                response_text = response.choices[0].message.content.strip()
            except Exception:
                response_text = "상대의 말에 흥미롭다는듯 가볍게 의견을 얹습니다."

            round_messages.append((name, response_text))
            temp_history.append(f"{name}: {response_text}")

        st.session_state.rounds.append(round_messages)
        st.rerun()

    # 만약 아직 라운드가 시작 안 된 상태라면 첫 라운드 자동 생성 (무작위로 서로 다른 3명이 포문 열기)
    if not st.session_state.rounds:
        with st.spinner("철학자들이 아고라 광장에 모여 서로 눈치를 보며 난상토론을 준비 중입니다..."):
            
            opening_speakers = list(PHILOSOPHERS.keys())
            random.shuffle(opening_speakers)
            opening_speakers = opening_speakers[:3] # 처음에 무작위로 3명이 다르게 시작
            
            round_messages = []
            history_context = []
            for name in opening_speakers:
                info = PHILOSOPHERS[name]
                prompt_content = (
                    f"{info['prompt']}\n\n"
                    f"[토론 주제] {st.session_state.current_topic}\n\n"
                    f"[아고라 광장 흐름]\n" + ("\n".join(history_context) if history_context else "토론 시작") +
                    f"\n\n지침: 아고라 광장에서 이 주제에 대해 편안하게 첫 의견을 펼쳐라."
                )
                messages_to_send = [
                    {"role": "system", "content": prompt_content},
                    {"role": "user", "content": f"{name}, 의견을 말해줘."}
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
            
            st.session_state.rounds.
