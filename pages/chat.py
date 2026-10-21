import os
import random
import time
from openai import OpenAI
import streamlit as st

# 페이지 기본 설정
st.set_page_config(page_title="🏛️ AI 철학자 아고라 카톡방", page_icon="🏛️")

st.title("🏛️ 고대 아고라 실시간 난상토론방")
st.write("주제를 입력하면 철학자들이 카카오톡 대화방처럼 실시간으로 길고 치열한 티키타카 토론을 벌입니다.")

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

# 3. 5인 철학자 페르소나 정의
PHILOSOPHERS = {
    "니체": {
        "icon": "⚡",
        "description": "기존 도덕을 해체하고 스스로 가치를 창조하라는 사상가",
        "prompt": (
            "너는 프레드리히 니체다.\n"
            "- 아고라 광장에서 앞사람의 위선적이거나 나약한 소리를 듣자마자, 차례를 기다리지 않고 곧바로 발끈하며 반박해라.\n"
            "- 메신저에서 툭 치고 들어가며 상대의 전제를 날카롭게 찌르고, 1~2줄로 짧고 자연스럽게 말해라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    },
    "소크라테스": {
        "icon": "🦉",
        "description": "무지의 자각을 이끌고 진리를 탐구하는 소탈한 철학자",
        "prompt": (
            "너는 소크라테스다.\n"
            "- 방금 누군가 한 말을 듣고는 피식 웃으며, '친구여, 정말 그런가?' 하고 허를 찌르는 반문을 1~2줄로 던져라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    },
    "장자": {
        "icon": "🦋",
        "description": "무위자연과 물아일체로 세속의 굴레를 가볍게 비워주는 도인",
        "prompt": (
            "너는 장자(莊子)다.\n"
            "- 사람들이 심각하게 열을 올릴 때, '다들 또 헛소리에 진심이네' 하듯 참지 못하고 툭 끼어들어 1~2줄로 비웃거나 농담을 던져라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    },
    "칸트": {
        "icon": "🕰️",
        "description": "보편적 도덕 법칙과 정언명령을 강조하는 원칙주의자",
        "prompt": (
            "너는 이마누엘 칸트다.\n"
            "- 앞사람이 도덕을 무시하면 정색하고 끼어들어 보편적 원칙을 1~2줄로 단호하게 들이밀어라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    },
    "홉스": {
        "icon": "🦁",
        "description": "만인의 만인에 대한 투쟁과 강력한 국가를 주장하는 현실주의자",
        "prompt": (
            "너는 토마스 홉스다.\n"
            "- 앞사람의 낙관적인 소리에 콧방귀를 뀌며 '나이브한 소리 집어치우세요' 하고 1~2줄로 현실을 짚어주어라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    }
}

# 4. 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "discussion_active" not in st.session_state:
    st.session_state.discussion_active = False
if "current_topic" not in st.session_state:
    st.session_state.current_topic = ""
if "step_count" not in st.session_state:
    st.session_state.step_count = 0

# 5. 토론 주제 입력창 (상단)
topic = st.text_input("아고라 대화방에 던질 토론 주제를 입력하세요:", placeholder="예: 착한 사마리아인법을 국가가 법으로 강제해야 하는가?")

if st.button("💬 대화방 입장 및 토론 시작"):
    if topic.strip():
        st.session_state.messages = []
        st.session_state.current_topic = topic
        st.session_state.discussion_active = True
        st.session_state.step_count = 0
        st.rerun()
    else:
        st.warning("토론 주제를 입력해 주세요.")

# 6. 카카오톡 대화방 형식 구현
if st.session_state.discussion_active:
    
    st.markdown("---")
    st.markdown(f"📌 **현재 토론 주제: {st.session_state.current_topic}**")
    st.markdown("---")

    # 대화방 내역 출력
    for chat in st.session_state.messages:
        if chat["type"] == "user_topic":
            st.info(chat["content"])
        elif chat["type"] == "chat":
            with st.chat_message("assistant", avatar=chat["icon"]):
                st.markdown(f"**{chat['speaker']}**")
                st.markdown(chat["content"])
        elif chat["type"] == "summary":
            with st.container():
                st.success(chat["content"])

    # 대화가 더 길게 이어지도록 MAX_STEPS를 8로 설정 (입론 1회 + 난상토론 6회 + 최종정리 1회)
    MAX_STEPS = 8  
    
    if st.session_state.step_count < MAX_STEPS:
        
        current_step = st.session_state.step_count
        
        if current_step == 0:
            spinner_msg = "🏛️ 5명의 철학자가 대화방에 모두 입장해 각자의 생각을 꺼내는 중..."
        elif current_step == MAX_STEPS - 1:
            spinner_msg = "📊 사회자가 대화 내용을 바탕으로 철학자별 주장을 정리하는 중..."
        else:
            spinner_msg = f"🔥 철학자들이 치열하게 티키타카를 주고받는 중... ({current_step}/{MAX_STEPS-1})"

        with st.spinner(spinner_msg):
            time.sleep(1.0)
            
            history_context = [f"{m['speaker']}: {m['content']}" for m in st.session_state.messages if m['type'] == 'chat']
            
            # 1단계 (step 0): 5명 철학자 전부 순서대로 자신의 첫 생각 입론
            if current_step == 0:
                for name, info in PHILOSOPHERS.items():
                    prompt_content = (
                        f"{info['prompt']}\n\n"
                        f"[토론 주제] {st.session_state.current_topic}\n\n"
                        f"지침: 대화방에 가장 먼저 입장하여, 이 주제에 대한 자신의 첫 번째 생각을 철학적 관점에서 1~2줄로 툭 던져라."
                    )
                    try:
                        res = client.chat.completions.create(
                            model="gemini-3.5-flash-lite",
                            messages=[
                                {"role": "system", "content": prompt_content},
                                {"role": "user", "content": "첫 생각을 말해줘."}
                            ],
                        )
                        text = res.choices[0].message.content.strip()
                    except Exception:
                        text = "이 주제에 대해 사색해 봅니다."
                    
                    st.session_state.messages.append({
                        "type": "chat",
                        "speaker": name,
                        "icon": info["icon"],
                        "content": text
                    })

            # 2 ~ (MAX_STEPS - 2) 단계: 실시간 난상토론 (무작위 3명이 티키타카 반박)
            elif current_step < MAX_STEPS - 1:
                selected_speakers = []
                temp_pool = list(PHILOSOPHERS.keys())
                random.shuffle(temp_pool)
                for s in temp_pool:
                    if s not in selected_speakers:
                        selected_speakers.append(s)
                    if len(selected_speakers) >= 3:
                        break

                temp_history = list(history_context)
                for name in selected_speakers:
                    info = PHILOSOPHERS[name]
                    prompt_content = (
                        f"{info['prompt']}\n\n"
                        f"[토론 주제] {st.session_state.current_topic}\n\n"
                        f"[대화방 흐름]\n" + ("\n".join(temp_history)) +
                        f"\n\n지침: 위 대화에서 방금 나온 다른 사람의 말에 꽂히거나 발끈해서 곧바로 1~2줄로 반박하거나 대화를 이어가라."
                    )
                    try:
                        res = client.chat.completions.create(
                            model="gemini-3.5-flash-lite",
                            messages=[
                                {"role": "system", "content": prompt_content},
                                {"role": "user", "content": "반박해줘."}
                            ],
                        )
                        text = res.choices[0].message.content.strip()
                    except Exception:
                        text = "동의할 수 없네요."
                    
                    st.session_state.messages.append({
                        "type": "chat",
                        "speaker": name,
                        "icon": info["icon"],
                        "content": text
                    })
                    temp_history.append(f"{name}: {text}")

            # 마지막 단계: 사회자의 깔끔한 정리
            else:
                summary_prompt = (
                    f"토론 주제: {st.session_state.current_topic}\n"
                    f"대화 내용:\n" + "\n".join(history_context) + "\n\n"
                    "지침: 지금까지 오간 대화 내용을 바탕으로, 사회자로서 각 철학자가 어떤 주장을 펼쳤는지 한눈에 보기 쉽게 정리해 줘.\n"
                    "반드시 아래 마크다운 형식(글머리 기호)으로만 깔끔하게 요약해 줘.\n"
                    "### 📊 [사회자] 철학자별 핵심 주장 요약\n"
                    "- **⚡ 니체**: ...\n"
                    "- **🦉 소크라테스**: ...\n"
                    "- **🦋 장자**: ...\n"
                    "- **🕰️ 칸트**: ...\n"
                    "- **🦁 홉스**: ..."
                )
                try:
                    res = client.chat.completions.create(
                        model="gemini-3.5-flash-lite",
                        messages=[{"role": "system", "content": summary_prompt}],
                    )
                    summary_text = res.choices[0].message.content.strip()
                except Exception:
                    summary_text = "토론 요약을 불러오지 못했습니다."

                st.session_state.messages.append({
                    "type": "summary",
                    "content": summary_text
                })

            st.session_state.step_count += 1
            st.rerun()

    else:
        st.success("🎉 토론이 모두 종료되었습니다!")
        if st.button("🔄 새로운 주제로 대화하기"):
            st.session_state.messages = []
            st.session_state.discussion_active = False
            st.session_state.step_count = 0
            st.rerun()
