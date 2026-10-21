import os
import random
import time
from datetime import datetime
from openai import OpenAI
import streamlit as st

# 페이지 기본 설정
st.set_page_config(page_title="🏛️ AI 철학자 아고라 카톡방", page_icon="🏛️", layout="centered")

# 카카오톡 스타일 Custom CSS
st.markdown("""
<style>
    .stApp {
        background-color: #BACEE0 !important;
    }
    
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 600px;
    }
    
    .kakaotalk-notice {
        background-color: rgba(0, 0, 0, 0.15);
        color: white;
        border-radius: 15px;
        padding: 8px 16px;
        text-align: center;
        font-size: 0.9rem;
        margin: 10px auto 25px auto;
        width: fit-content;
        font-weight: bold;
    }

    .kakao-msg-container {
        display: flex;
        margin-bottom: 22px;
        align-items: flex-start;
    }
    
    .kakao-avatar {
        width: 42px;
        height: 42px;
        border-radius: 16px;
        background-color: #FFE812;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.4rem;
        margin-right: 10px;
        flex-shrink: 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .kakao-content {
        display: flex;
        flex-direction: column;
    }
    
    .kakao-name {
        font-size: 0.82rem;
        color: #333333;
        margin-bottom: 5px;
        font-weight: bold;
    }
    
    .kakao-bubble-wrapper {
        display: flex;
        align-items: flex-end;
    }
    
    .kakao-bubble {
        background-color: #FFFFFF;
        color: #111111;
        padding: 11px 15px;
        border-radius: 15px;
        border-top-left-radius: 2px;
        font-size: 0.98rem;
        line-height: 1.4;
        max-width: 340px;
        word-break: break-word;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }
    
    .kakao-time {
        font-size: 0.72rem;
        color: #4B637E;
        margin-left: 6px;
        white-space: nowrap;
    }

    /* 사회자 최종 요약 카드 스타일 */
    .summary-card {
        background-color: #FFFFFF;
        border-radius: 16px;
        padding: 22px;
        margin-top: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        color: #111111;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏛️ AI 철학자 그룹채팅")

# 1. API 키 가져오기
try:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("secrets.toml 파일에서 GEMINI_API_KEY를 찾을 수 없습니다.")
    st.stop()

# 2. OpenAI 클라이언트 설정
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
            "- 토론 중에는 절대 길게 말하지 마라. 무조건 **1~2문장**으로 짧고 툭 던지듯 반박해라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    },
    "소크라테스": {
        "icon": "🦉",
        "description": "무지의 자각을 이끌고 진리를 탐구하는 소탈한 철학자",
        "prompt": (
            "너는 소크라테스다.\n"
            "- 토론 중에는 절대 길게 말하지 마라. 무조건 **1~2문장**으로 짧게 반문해라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    },
    "장자": {
        "icon": "🦋",
        "description": "무위자연과 물아일체로 세속의 굴레를 가볍게 비워주는 도인",
        "prompt": (
            "너는 장자(莊子)다.\n"
            "- 토론 중에는 절대 길게 말하지 마라. 무조건 **1~2문장**으로 허를 찌르는 농담을 해라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    },
    "칸트": {
        "icon": "🕰️",
        "description": "보편적 도덕 법칙과 정언명령을 강조하는 원칙주의자",
        "prompt": (
            "너는 이마누엘 칸트다.\n"
            "- 토론 중에는 절대 길게 말하지 마라. 무조건 **1~2문장**으로 단호하게 원칙을 말해라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    },
    "홉스": {
        "icon": "🦁",
        "description": "만인의 만인에 대한 투쟁과 강력한 국가를 주장하는 현실주의자",
        "prompt": (
            "너는 토마스 홉스다.\n"
            "- 토론 중에는 절대 길게 말하지 마라. 무조건 **1~2문장**으로 냉철하게 팩트를 꽂아라.\n"
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

# 5. 토론 주제 입력 영역
topic = st.text_input("아고라 채팅방에 던질 토론 주제를 입력하세요:", placeholder="예: 착한 사마리아인법을 국가가 법으로 강제해야 하는가?")

if st.button("💬 채팅방 입장 및 토론 시작"):
    if topic.strip():
        st.session_state.messages = []
        st.session_state.current_topic = topic
        st.session_state.discussion_active = True
        st.session_state.step_count = 0
        st.rerun()
    else:
        st.warning("토론 주제를 입력해 주세요.")

# 6. 카카오톡 대화방 화면 렌더링
if st.session_state.discussion_active:
    
    st.markdown(f'<div class="kakaotalk-notice">📌 [토론 주제] {st.session_state.current_topic}</div>', unsafe_allow_html=True)

    for chat in st.session_state.messages:
        if chat["type"] == "chat":
            st.markdown(f"""
            <div class="kakao-msg-container">
                <div class="kakao-avatar">{chat['icon']}</div>
                <div class="kakao-content">
                    <div class="kakao-name">{chat['speaker']}</div>
                    <div class="kakao-bubble-wrapper">
                        <div class="kakao-bubble">{chat['content'].replace('\n', '<br>')}</div>
                        <div class="kakao-time">{chat['time']}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        elif chat["type"] == "summary":
            st.markdown(f"""
            <div class="summary-card">
                {chat['content'].replace('\n', '<br>')}
            </div>
            """, unsafe_allow_html=True)

    MAX_STEPS = 8  # 입론 1회 + 난상토론 6회 + 요약 1회
    
    if st.session_state.step_count < MAX_STEPS:
        
        current_step = st.session_state.step_count
        now_time = datetime.now().strftime("%p %I:%M").replace("AM", "오전").replace("PM", "오후")
        
        if current_step == 0:
            spinner_msg = "🏛️ 철학자들이 입장해 진중한 첫 입론을 펼치는 중..."
        elif current_step == MAX_STEPS - 1:
            spinner_msg = "📊 사회자가 토론 내용을 바탕으로 핵심 주장을 정리하는 중..."
        else:
            spinner_msg = f"🔥 톡으로 티키타카 수다를 떠는 중... ({current_step}/{MAX_STEPS-1})"

        with st.spinner(spinner_msg):
            time.sleep(1.0)
            
            history_context = [f"{m['speaker']}: {m['content']}" for m in st.session_state.messages if m['type'] == 'chat']
            
            # 1단계: 초반 입론 (3~4문장)
            if current_step == 0:
                for name, info in PHILOSOPHERS.items():
                    intro_prompt = (
                        f"{info['prompt']}\n\n"
                        f"[토론 주제] {st.session_state.current_topic}\n\n"
                        f"지침: 채팅방에 엄숙하게 입장하여, 이 주제에 대한 자신의 첫 생각을 **깊이 있고 진중한 사상을 담아 3~4문장**으로 길게 발표해라."
                    )
                    try:
                        res = client.chat.completions.create(
                            model="gemini-3.5-flash-lite",
                            messages=[
                                {"role": "system", "content": intro_prompt},
                                {"role": "user", "content": "진중한 첫 입론을 시작해줘."}
                            ],
                        )
                        text = res.choices[0].message.content.strip()
                    except Exception:
                        text = "이 주제는 우리에게 깊은 사색을 요구합니다. 신중하게 접근해야 합니다."
                    
                    st.session_state.messages.append({
                        "type": "chat",
                        "speaker": name,
                        "icon": info["icon"],
                        "content": text,
                        "time": now_time
                    })

            # 난상토론 단계 (1~2문장)
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
                        f"\n\n지침: 방금 올라온 톡에 발끈하거나 반박하며 무조건 **1~2문장**으로 짧게 쳐내라."
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
                        text = "아니지, 그건 아니지."
                    
                    st.session_state.messages.append({
                        "type": "chat",
                        "speaker": name,
                        "icon": info["icon"],
                        "content": text,
                        "time": now_time
                    })
                    temp_history.append(f"{name}: {text}")

            # 사회자 최종 요약 카드 생성
            else:
                summary_prompt = (
                    f"토론 주제: {st.session_state.current_topic}\n"
                    f"대화 내용:\n" + "\n".join(history_context) + "\n\n"
                    "지침: 지금까지 오간 토론 내용을 바탕으로, 사회자로서 각 철학자가 이번 주제에 대해 어떤 핵심 주장을 펼쳤는지 알기 쉽게 정리해 줘.\n"
                    "반드시 아래 형식으로만 작성할 것:\n"
                    "### 📊 [사회자] 철학자별 핵심 주장 요약\n"
                    "- **⚡ 니체**: (주제에 대한 핵심 입장)\n"
                    "- **🦉 소크라테스**: (주제에 대한 핵심 입장)\n"
                    "- **🦋 장자**: (주제에 대한 핵심 입장)\n"
                    "- **🕰️ 칸트**: (주제에 대한 핵심 입장)\n"
                    "- **🦁 홉스**: (주제에 대한 핵심 입장)"
                )
                try:
                    res = client.chat.completions.create(
                        model="gemini-3.5-flash-lite",
                        messages=[{"role": "system", "content": summary_prompt}],
                    )
                    summary_text = res.choices[0].message.content.strip()
                except Exception:
                    summary_text = (
                        "### 📊 [사회자] 철학자별 핵심 주장 요약\n"
                        "- **⚡ 니체**: 기존 도덕을 해체하고 스스로 가치를 세울 것.\n"
                        "- **🦉 소크라테스**: 끊임없는 질문으로 무지를 깨달을 것.\n"
                        "- **🦋 장자**: 세속적 잣대를 벗어나 무위자연을 따를 것.\n"
                        "- **🕰️ 칸트**: 보편적 도덕 법칙과 의무를 지킬 것.\n"
                        "- **🦁 홉스**: 강력한 질서와 규범으로 이기심을 통제할 것."
                    )

                st.session_state.messages.append({
                    "type": "summary",
                    "content": summary_text
                })

            st.session_state.step_count += 1
            st.rerun()

    else:
        # 토론 종료 알림 및 재시작 버튼
        st.success("🎉 아고라 광장의 열띤 토론이 모두 종료되었습니다!")
        if st.button("🔄 새로운 주제로 대화하기"):
            st.session_state.messages = []
            st.session_state.discussion_active = False
            st.session_state.step_count = 0
            st.rerun()
