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
        margin-bottom: 4px;
    }
    
    .kakao-bubble {
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
    
    .kakao-time {
        font-size: 0.72rem;
        color: #4B637E;
        margin-left: 6px;
        white-space: nowrap;
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

# 3. 5인 철학자 페르소나 정의 (고등학생 눈높이 + 짧고 쉬운 어휘 반영)
PHILOSOPHERS = {
    "니체": {
        "icon": "⚡",
        "description": "기존 도덕을 깨부수고 스스로 가치를 만들라는 사상가",
        "prompt": (
            "너는 프레드리히 니체다.\n"
            "- 고등학생도 이해할 수 있게 쉬운 단어로 말해라. 어렵고 딱딱한 철학 용어는 피해라.\n"
            "- '기존의 틀이나 뻔한 도덕을 깨고 스스로 주인이 되어라'라는 핵심 개념을 강조해라.\n"
            "- 토론 중에는 1~2문장으로 짧게 반박해라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    },
    "소크라테스": {
        "icon": "🦉",
        "description": "질문을 통해 자신의 무지를 깨닫게 하는 철학자",
        "prompt": (
            "너는 소크라테스다.\n"
            "- 고등학생도 이해할 수 있게 쉬운 단어로 말해라.\n"
            "- '우리가 정말 제대로 알고 있는지 스스로 돌아봐야 한다'는 무지의 자각 개념을 강조하며 1~2문장으로 질문을 던져라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    },
    "장자": {
        "icon": "🦋",
        "description": "자연의 흐름에 맡기고 억지로 하지 말라는 도인",
        "prompt": (
            "너는 장자(莊子)다.\n"
            "- 고등학생도 이해할 수 있게 가볍고 쉬운 단어로 말해라.\n"
            "- '억지로 얽매이지 말고 자연스럽게(무위자연) 흘러가자'는 핵심 생각을 담아 1~2문장으로 재치 있게 말해라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    },
    "칸트": {
        "icon": "🕰️",
        "description": "누구나 지켜야 할 보편적인 도덕 원칙을 강조하는 원칙주의자",
        "prompt": (
            "너는 이마누엘 칸트다.\n"
            "- 고등학생도 쉽게 알아들을 수 있게 표현해라.\n"
            "- '누구에게나 적용되는 보편적인 도덕 법칙과 의무를 지켜야 한다'는 핵심을 담아 1~2문장으로 단호하게 말해라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    },
    "홉스": {
        "icon": "🦁",
        "description": "인간의 이기심을 막기 위해 강력한 법과 질서가 필요하다는 현실주의자",
        "prompt": (
            "너는 토마스 홉스다.\n"
            "- 고등학생 수준에 맞춰 쉽고 현실적인 단어를 써라.\n"
            "- '사람은 이기적이어서 강력한 법과 통제가 없으면 혼란에 빠진다'는 생각을 담아 1~2문장으로 팩트를 짚어라.\n"
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

    # 이전 대화 출력
    for chat in st.session_state.messages:
        if chat["type"] == "chat":
            # 초반 입론은 한 말풍선으로, 이후 난상토론은 문장별 말풍선으로 쪼개서 출력
            lines = chat["lines"]
            
            bubbles_html = ""
            for idx, line in enumerate(lines):
                # 마지막 문장에만 시간 표시
                time_html = f'<div class="kakao-time">{chat["time"]}</div>' if idx == len(lines) - 1 else ''
                bubbles_html += f"""
                <div class="kakao-bubble-wrapper">
                    <div class="kakao-bubble">{line}</div>
                    {time_html}
                </div>
                """
            
            st.markdown(f"""
            <div class="kakao-msg-container">
                <div class="kakao-avatar">{chat['icon']}</div>
                <div class="kakao-content">
                    <div class="kakao-name">{chat['speaker']}</div>
                    {bubbles_html}
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
            spinner_msg = "🏛️ 철학자들이 입장해 첫 생각을 진중하게 발표하는 중..."
        elif current_step == MAX_STEPS - 1:
            spinner_msg = "📊 사회자가 고등학생도 쉽게 알 수 있게 핵심 주장을 정리하는 중..."
        else:
            spinner_msg = f"🔥 톡으로 티키타카 수다를 떠는 중... ({current_step}/{MAX_STEPS-1})"

        with st.spinner(spinner_msg):
            time.sleep(0.8)
            
            # 대화 기록 텍스트 조합
            flat_history = []
            for m in st.session_state.messages:
                if m['type'] == 'chat':
                    flat_history.append(f"{m['speaker']}: {' '.join(m['lines'])}")

            # 1단계: 초반 입론 (한 말풍선에 2~3문장 포함)
            if current_step == 0:
                for name, info in PHILOSOPHERS.items():
                    intro_prompt = (
                        f"{info['prompt']}\n\n"
                        f"[토론 주제] {st.session_state.current_topic}\n\n"
                        f"지침:\n"
                        f"1. 이 주제에 대한 너의 철학적 생각을 2~3문장으로 진중하게 밝혀라.\n"
                        f"2. 어렵고 복잡한 사상 용어 대신, 고등학생이 직관적으로 이해할 수 있는 쉬운 어휘를 써라."
                    )
