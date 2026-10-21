import os
import random
import time
from datetime import datetime
from openai import OpenAI
import streamlit as st

# 페이지 기본 설정
st.set_page_config(page_title="🏛️ AI 철학자 아고라 카톡방", page_icon="🏛️", layout="centered")

# 1. 카카오톡 스타일 Custom CSS 적용
st.markdown("""
<style>
    /* 전체 배경을 카카오톡 파란 배경색으로 변경 */
    .main {
        background-color: #BACEE0;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 600px;
    }
    
    /* 상단 안내 박스 */
    .kakaotalk-notice {
        background-color: rgba(0, 0, 0, 0.15);
        color: white;
        border-radius: 15px;
        padding: 8px 16px;
        text-align: center;
        font-size: 0.85rem;
        margin: 10px auto 20px auto;
        width: fit-content;
    }

    /* 카카오톡 메시지 컨테이너 (왼쪽 철학자 발언) */
    .kakao-msg-container {
        display: flex;
        margin-bottom: 15px;
        align-items: flex-start;
    }
    
    /* 프로필 아이콘 */
    .kakao-avatar {
        width: 42px;
        height: 42px;
        border-radius: 15px;
        background-color: #FFE812;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.4rem;
        margin-right: 8px;
        flex-shrink: 0;
    }
    
    .kakao-content {
        display: flex;
        flex-direction: column;
    }
    
    /* 철학자 이름 */
    .kakao-name {
        font-size: 0.8rem;
        color: #424242;
        margin-bottom: 4px;
        font-weight: bold;
    }
    
    .kakao-bubble-wrapper {
        display: flex;
        align-items: flex-end;
    }
    
    /* 흰색 말풍선 */
    .kakao-bubble {
        background-color: #FFFFFF;
        color: #000000;
        padding: 9px 13px;
        border-radius: 14px;
        border-top-left-radius: 2px;
        font-size: 0.95rem;
        line-height: 1.4;
        max-width: 320px;
        word-break: break-word;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    
    /* 전송 시간 */
    .kakao-time {
        font-size: 0.7rem;
        color: #556677;
        margin-left: 5px;
        white-space: nowrap;
    }

    /* 사회자 정리 상자 */
    .summary-box {
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: 15px;
        padding: 15px 20px;
        margin-top: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        color: #222222;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏛️ AI 철학자 그룹채팅")

# 2. API 키 가져오기
try:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("secrets.toml 파일에서 GEMINI_API_KEY를 찾을 수 없습니다.")
    st.stop()

# 3. OpenAI 라이브러리 호환 Gemini 클라이언트 생성
client = OpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# 4. 5인 철학자 페르소나 정의
PHILOSOPHERS = {
    "니체": {
        "icon": "⚡",
        "description": "기존 도덕을 해체하고 스스로 가치를 창조하라는 사상가",
        "prompt": (
            "너는 프레드리히 니체다.\n"
            "- 첫 입론에서는 진중하고 깊이 있는 사색을 담아 3~4문장으로 소신을 밝혀라.\n"
            "- 토론 중에는 상대방의 위선적인 태도를 날카롭게 찌르는 반박을 1~2줄로 짧게 건네라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    },
    "소크라테스": {
        "icon": "🦉",
        "description": "무지의 자각을 이끌고 진리를 탐구하는 소탈한 철학자",
        "prompt": (
            "너는 소크라테스다.\n"
            "- 첫 입론에서는 질문을 포함해 진중한 성찰을 3~4문장으로 펼쳐라.\n"
            "- 토론 중에는 '친구여, 정말 그런가?' 하고 허를 찌르는 반문을 1~2줄로 던져라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    },
    "장자": {
        "icon": "🦋",
        "description": "무위자연과 물아일체로 세속의 굴레를 가볍게 비워주는 도인",
        "prompt": (
            "너는 장자(莊子)다.\n"
            "- 첫 입론에서는 세속적 규범의 부질없음을 3~4문장으로 깊이 있게 이야기해라.\n"
            "- 토론 중에는 헛소리에 진심인 이들을 비웃거나 1~2줄로 가벼운 농담을 던져라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    },
    "칸트": {
        "icon": "🕰️",
        "description": "보편적 도덕 법칙과 정언명령을 강조하는 원칙주의자",
        "prompt": (
            "너는 이마누엘 칸트다.\n"
            "- 첫 입론에서는 정언명령과 보편적 도덕 법칙의 관점에서 3~4문장으로 발표해라.\n"
            "- 토론 중에는 도덕을 무시하는 태도에 정색하고 1~2줄로 단호하게 반박해라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    },
    "홉스": {
        "icon": "🦁",
        "description": "만인의 만인에 대한 투쟁과 강력한 국가를 주장하는 현실주의자",
        "prompt": (
            "너는 토마스 홉스다.\n"
            "- 첫 입론에서는 이기적 본성과 질서의 필요성을 3~4문장으로 묵직하게 밝혀라.\n"
            "- 토론 중에는 나이브한 소리에 콧방귀를 뀌며 1~2줄로 현실을 짚어주어라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    }
}

# 5. 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "discussion_active" not in st.session_state:
    st.session_state.discussion_active = False
if "current_topic" not in st.session_state:
    st.session_state.current_topic = ""
if "step_count" not in st.session_state:
    st.session_state.step_count = 0

# 6. 토론 주제 입력 영역
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

# 7. 카카오톡 대화방 화면 렌더링
if st.session_state.discussion_active:
    
    # 카카오톡 상단 공지/날짜 스타일
    st.markdown(f'<div class="kakaotalk-notice">📌 [토론 주제] {st.session_state.current_topic}</div>', unsafe_allow_html=True)

    # 이전 대화 출력 (카톡 스타일 HTML Render)
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
            <div class="summary-box">
                {chat['content'].replace('\n', '<br>')}
            </div>
            """, unsafe_allow_html=True)

    MAX_STEPS = 8  # 입론 1회 + 난상토론 6회 + 요약 1회
    
    if st.session_state.step_count < MAX_STEPS:
        
        current_step = st.session_state.step_count
        now_time = datetime.now().strftime("%p %I:%M").replace("AM", "오전").replace("PM", "오후")
        
        if current_step == 0:
            spinner_msg = "🏛️ 철학자들이 대화방에 입장하여 첫 입론을 준비 중..."
        elif current_step == MAX_STEPS - 1:
            spinner_msg = "📊 사회자가 대화 내용을 정리하는 중..."
        else:
            spinner_msg = f"🔥 철학자들이 티키타카를 주고받는 중... ({current_step}/{MAX_STEPS-1})"

        with st.spinner(spinner_msg):
            time.sleep(1.0)
            
            history_context = [f"{m['speaker']}: {m['content']}" for m in st.session_state.messages if m['type'] == 'chat']
            
            # 1단계: 진중한 첫 입론
            if current_step == 0:
                for name, info in PHILOSOPHERS.items():
                    prompt_content = (
                        f"{info['prompt']}\n\n"
                        f"[토론 주제] {st.session_state.current_topic}\n\n"
                        f"지침: 채팅방에 엄숙하게 입장하여, 이 주제에 대한 자신의 첫 생각을 진중하게 3~4문장으로 밝혀라."
                    )
                    try:
                        res = client.chat.completions.create(
                            model="gemini-3.5-flash-lite",
                            messages=[
                                {"role": "system", "content": prompt_content},
                                {"role": "user", "content": "첫 입론을 말해줘."}
                            ],
                        )
                        text = res.choices[0].message.content.strip()
                    except Exception:
                        text = "이 주제는 사색해 볼 가치가 있군요."
                    
                    st.session_state.messages.append({
                        "type": "chat",
                        "speaker": name,
                        "icon": info["icon"],
                        "content": text,
                        "time": now_time
                    })

            # 난상토론 단계
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
                        f"\n\n지침: 방금 나온 말에 즉각 반박하여 1~2줄로 말해라."
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
                        text = "동의할 수 없습니다."
                    
                    st.session_state.messages.append({
                        "type": "chat",
                        "speaker": name,
                        "icon": info["icon"],
                        "content": text,
                        "time": now_time
                    })
                    temp_history.append(f"{name}: {text}")

            # 사회자 최종 요약
            else:
                summary_prompt = (
                    f"토론 주제: {st.session_state.current_topic}\n"
                    f"대화 내용:\n" + "\n".join(history_context) + "\n\n"
                    "지침: 지금까지 오간 대화 내용을 바탕으로 사회자로서 각 철학자의 핵심 주장을 요약해라.\n"
                    "반드시 아래 마크다운 형식으로만 정리할 것:\n"
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
                    summary_text = (
                        "### 📊 [사회자] 철학자별 핵심 주장 요약\n"
                        "- **⚡ 니체**: 기존 도덕을 해체하고 스스로의 가치를 세울 것을 강조함.\n"
                        "- **🦉 소크라테스**: 끊임없는 질문을 통해 무지를 깨닫고 진리를 탐구함.\n"
                        "- **🦋 장자**: 세속적 잣대에서 벗어난 무위자연의 삶을 주장함.\n"
                        "- **🕰️ 칸트**: 보편적 도덕 법칙과 의무를 최우선으로 삼음.\n"
                        "- **🦁 홉스**: 인간의 이기심을 통제할 강력한 질서와 사회 계약을 역설함."
                    )

                st.session_state.messages.append({
                    "type": "summary",
                    "content": summary_text
                })

            st.session_state.step_count += 1
            st.rerun()

    else:
        st.success("🎉 토론이 종료되었습니다!")
        if st.button("🔄 새로운 주제로 대화하기"):
            st.session_state.messages = []
            st.session_state.discussion_active = False
            st.session_state.step_count = 0
            st.rerun()
