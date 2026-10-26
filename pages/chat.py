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

    .kakao-msg-row {
        display: flex;
        margin-bottom: 14px;
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
    
    .kakao-info-col {
        display: flex;
        flex-direction: column;
    }
    
    .kakao-sender {
        font-size: 0.82rem;
        color: #333333;
        margin-bottom: 5px;
        font-weight: bold;
    }
    
    .kakao-bubble-line {
        display: flex;
        align-items: flex-end;
        margin-bottom: 4px;
    }
    
    .kakao-bubble-box {
        background-color: #FFFFFF;
        color: #111111;
        padding: 10px 14px;
        border-radius: 14px;
        border-top-left-radius: 2px;
        font-size: 0.95rem;
        line-height: 1.4;
        max-width: 340px;
        word-break: break-word;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }
    
    .kakao-timestamp {
        font-size: 0.72rem;
        color: #4B637E;
        margin-left: 6px;
        white-space: nowrap;
        flex-shrink: 0;
    }

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

# 3. 5인 철학자 페르소나 정의 (고등학생 눈높이 + 구체적인 반박 유도)
PHILOSOPHERS = {
    "니체": {
        "icon": "⚡",
        "description": "기존 도덕을 깨부수고 스스로 가치를 만들라는 사상가",
        "prompt": "너는 프레드리히 니체다. 상대의 말에 단순 동조하거나 뻔한 비판을 하지 말고, 기존의 틀을 깨는 너만의 새로운 주장을 1~2문장으로 선언해라. 고등학생이 이해하기 쉽게 쉬운 단어를 써라."
    },
    "소크라테스": {
        "icon": "🦉",
        "description": "질문을 통해 자신의 무지를 깨닫게 하는 철학자",
        "prompt": "너는 소크라테스다. 상대의 말에 뻔한 답변을 피하고, 우리가 놓치고 있는 본질을 찌르는 새로운 질문이나 주장을 1~2문장으로 던져라. 고등학생이 이해하기 쉽게 쉬운 단어를 써라."
    },
    "장자": {
        "icon": "🦋",
        "description": "자연의 흐름에 맡기고 억지로 하지 말라는 도인",
        "prompt": "너는 장자다. 상대의 말에 얽매이지 말고, 억지 규율을 벗어나 자연스럽게 흐르자는 너만의 새로운 관점을 1~2문장으로 재치 있게 제시해라. 고등학생이 이해하기 쉽게 쉬운 단어를 써라."
    },
    "칸트": {
        "icon": "🕰️",
        "description": "누구나 지켜야 할 보편적인 도덕 원칙을 강조하는 원칙주의자",
        "prompt": "너는 이마누엘 칸트다. 상대의 주장에 흔들리지 말고, 보편적인 의무와 도덕 법칙에 근거한 확고하고 새로운 주장을 1~2문장으로 단호하게 말해라. 고등학생이 이해하기 쉽게 쉬운 단어를 써라."
    },
    "홉스": {
        "icon": "🦁",
        "description": "인간의 이기심을 막기 위해 강력한 법과 질서가 필요하다는 현실주의자",
        "prompt": "너는 토마스 홉스다. 나이브한 주장을 깎아내리며, 인간의 이기심을 통제할 강력한 질서가 왜 필요한지 새로운 현실적 논거를 1~2문장으로 제시해라. 고등학생이 이해하기 쉽게 쉬운 단어를 써라."
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

    # 대화 출력
    for chat in st.session_state.messages:
        if chat["type"] == "chat":
            lines = chat["lines"]
            speaker = chat["speaker"]
            icon = chat["icon"]
            time_str = chat["time"]
            
            st.markdown(f"""
            <div class="kakao-msg-row">
                <div class="kakao-avatar">{icon}</div>
                <div class="kakao-info-col">
                    <div class="kakao-sender">{speaker}</div>
            """, unsafe_allow_html=True)
            
            for idx, line in enumerate(lines):
                is_last = (idx == len(lines) - 1)
                time_div = f'<div class="kakao-timestamp">{time_str}</div>' if is_last else ''
                
                st.markdown(f"""
                <div class="kakao-bubble-line">
                    <div class="kakao-bubble-box">{line}</div>
                    {time_div}
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("</div></div>", unsafe_allow_html=True)
            
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
            spinner_msg = "🏛️ 철학자들이 입장해 첫 생각을 진중하게 발표하는 중..."
        elif current_step == MAX_STEPS - 1:
            spinner_msg = "📊 사회자가 고등학생도 쉽게 알 수 있게 핵심 주장을 정리하는 중..."
        else:
            spinner_msg = f"🔥 톡으로 티키타카 수다를 떠는 중... ({current_step}/{MAX_STEPS-1})"

        with st.spinner(spinner_msg):
            time.sleep(0.8)
            
            flat_history = []
            for m in st.session_state.messages:
                if m['type'] == 'chat':
                    flat_history.append(f"{m['speaker']}: {' '.join(m['lines'])}")

            # 1단계: 초반 입론 (문장별 분리)
            if current_step == 0:
                for name, info in PHILOSOPHERS.items():
                    intro_prompt = (
                        f"{info['prompt']}\n\n"
                        f"[토론 주제] {st.session_state.current_topic}\n\n"
                        f"지침: 이 주제에 대한 너의 철학적 입장을 2~3문장으로 진중하게 밝혀라. 고등학생이 직관적으로 이해할 수 있는 쉬운 어휘를 써라."
                    )
                    try:
                        res = client.chat.completions.create(
                            model="gemini-3.5-flash-lite",
                            messages=[
                                {"role": "system", "content": intro_prompt},
                                {"role": "user", "content": "첫 생각을 말해줘."}
                            ],
                        )
                        text = res.choices[0].message.content.strip()
                    except Exception:
                        text = "이 주제는 우리가 다 같이 깊이 고민해봐야 할 중요한 문제입니다."
                    
                    sentences = [s.strip() for s in text.replace('!', '!|').replace('?', '?|').replace('.', '.|').split('|') if s.strip()]
                    if not sentences:
                        sentences = [text]

                    st.session_state.messages.append({
                        "type": "chat",
                        "speaker": name,
                        "icon": info["icon"],
                        "lines": sentences,
                        "time": now_time
                    })

            # 난상토론 단계 (새로운 주장과 논거 제시)
            elif current_step < MAX_STEPS - 1:
                selected_speakers = []
                temp_pool = list(PHILOSOPHERS.keys())
                random.shuffle(temp_pool)
                for s in temp_pool:
                    if s not in selected_speakers:
                        selected_speakers.append(s)
                    if len(selected_speakers) >= 3:
                        break

                temp_history = list(flat_history)
                for name in selected_speakers:
                    info = PHILOSOPHERS[name]
                    prompt_content = (
                        f"{info['prompt']}\n\n"
                        f"[토론 주제] {st.session_state.current_topic}\n\n"
                        f"[대화방 흐름]\n" + ("\n".join(temp_history)) +
                        f"\n\n지침: 직전 대화에 얽매이지 말고, 이 주제를 향한 **너만의 새로운 주장이나 날카로운 논거**를 1~2문장으로 새롭게 꺼내어 말해라."
                    )
                    try:
                        res = client.chat.completions.create(
                            model="gemini-3.5-flash-lite",
                            messages=[
                                {"role": "system", "content": prompt_content},
                                {"role": "user", "content": "새로운 주장을 펼쳐줘."}
                            ],
                        )
                        text = res.choices[0].message.content.strip()
                    except Exception:
                        text = "오히려 이 문제는 다른 각도에서 바라보아야 합니다."
                    
                    sentences = [s.strip() for s in text.replace('!', '!|').replace('?', '?|').replace('.', '.|').split('|') if s.strip()]
                    if not sentences:
                        sentences = [text]

                    st.session_state.messages.append({
                        "type": "chat",
                        "speaker": name,
                        "icon": info["icon"],
                        "lines": sentences,
                        "time": now_time
                    })
                    temp_history.append(f"{name}: {text}")

            # 사회자 최종 요약 카드 생성
            else:
                summary_prompt = (
                    f"토론 주제: {st.session_state.current_topic}\n"
                    f"대화 내용:\n" + "\n".join(flat_history) + "\n\n"
                    f"지침: 지금까지 오간 대화 내용을 바탕으로, 사회자로서 이번 주제('{st.session_state.current_topic}')에 대해 각 철학자가 어떤 주장을 펼쳤는지 정리해 줘.\n"
                    f"고등학생이 읽고 한눈에 이해할 수 있도록 쉽고 명확한 어휘로 정리해야 해.\n"
                    "반드시 아래 마크다운 형식으로만 작성할 것:\n"
                    f"### 📊 [사회자] '{st.session_state.current_topic}'에 대한 철학자별 핵심 주장\n"
                    "- **⚡ 니체**: (고등학생 눈높이의 핵심 주장 1문장)\n"
                    "- **🦉 소크라테스**: (고등학생 눈높이의 핵심 주장 1문장)\n"
                    "- **🦋 장자**: (고등학생 눈높이의 핵심 주장 1문장)\n"
                    "- **🕰️ 칸트**: (고등학생 눈높이의 핵심 주장 1문장
