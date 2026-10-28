import os
import random
import time
from datetime import datetime
from openai import OpenAI
import streamlit as st

# 페이지 기본 설정
st.set_page_config(page_title="🏛️ AI 철학자 아고라 카톡방", page_icon="🏛️", layout="centered")

# 카카오톡 스타일 Custom CSS (상단 고정바 관련 스타일만 제거)
st.markdown("""
<style>
    .stApp {
        background-color: #BACEE0 !important;
    }
    
    .block-container {
        padding-top: 1rem;
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

# 페이지 최상단 앵커
st.markdown('<div id="top-anchor"></div>', unsafe_allow_html=True)

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

# 3. 5인 철학자 페르소나 정의 (철학자별 고유 색상 및 이름 호칭 규칙 부여)
PHILOSOPHERS = {
    "니체": {
        "icon": "⚡",
        "color": "#D32F2F", # 강렬한 빨강
        "description": "기존 도덕을 깨부수고 스스로 가치를 만들라는 사상가",
        "prompt": "너는 프레드리히 니체다. 고등학생도 이해하기 쉽게 쉬운 단어로 대답해라. 상대방을 부를 때 '네'라는 호칭을 남발하지 말고, 상대방의 이름(소크라테스, 장자, 칸트, 홉스 중 한 명)을 자연스럽게 언급하며 그 주장을 예리하게 반박해라. 반드시 순수 한국어로만 1~2문장으로 답해라."
    },
    "소크라테스": {
        "icon": "🦉",
        "color": "#1976D2", # 신중한 파랑
        "description": "질문을 통해 자신의 무지를 깨닫게 하는 철학자",
        "prompt": "너는 소크라테스다. 고등학생도 이해하기 쉽게 쉬운 단어로 대답해라. '네'라는 호칭은 최소화하고, 반박할 상대의 이름(니체, 장자, 칸트, 홉스 중 한 명)을 직접 부르며 날카로운 질문이나 반문을 던져라. 반드시 순수 한국어로만 1~2문장으로 답해라."
    },
    "장자": {
        "icon": "🦋",
        "color": "#388E3C", # 자연의 초록
        "description": "자연의 흐름에 맡기고 억지로 하지 말라는 도인",
        "prompt": "너는 장자다. 고등학생도 이해하기 쉽게 쉬운 단어로 대답해라. '네'라는 호칭 대신 상대방의 이름(니체, 소크라테스, 칸트, 홉스 중 한 명)을 언급하며 억지스러운 주장을 재치 있게 받아쳐라. 반드시 순수 한국어로만 1~2문장으로 답해라."
    },
    "칸트": {
        "icon": "🕰️",
        "color": "#7B1FA2", # 원칙의 보라
        "description": "누구나 지켜야 할 보편적인 도덕 원칙을 강조하는 원칙주의자",
        "prompt": "너는 이마누엘 칸트다. 고등학생도 쉽게 대답해라. '네'라는 호칭을 자제하고, 상대방의 이름(니체, 소크라테스, 장자, 홉스 중 한 명)을 부르며 도덕적 의무와 원칙을 저버렸다고 단호하게 반박해라. 반드시 순수 한국어로만 1~2문장으로 답해라."
    },
    "홉스": {
        "icon": "🦁",
        "color": "#E65100", # 현실의 주황
        "description": "인간의 이기심을 막기 위해 강력한 법과 질서가 필요하다는 현실주의자",
        "prompt": "너는 토마스 홉스다. 고등학생 수준에 맞춰 대답해라. '네'라는 호칭보다는 상대방의 이름(니체, 소크라테스, 장자, 칸트 중 한 명)을 직접 언급하며 현실성 없는 공상이라 팩트를 짚어 반박해라. 반드시 순수 한국어로만 1~2문장으로 답해라."
    }
}

# 텍스트 내 철학자 이름에 고유 색상을 입혀주는 헬퍼 함수
def colorize_philosopher_names(text):
    for name, info in PHILOSOPHERS.items():
        colored_tag = f"<span style='color: {info['color']}; font-weight: bold;'>{name}</span>"
        text = text.replace(name, colored_tag)
    return text

# 4. 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "discussion_active" not in st.session_state:
    st.session_state.discussion_active = False
if "current_topic" not in st.session_state:
    st.session_state.current_topic = ""
if "step_count" not in st.session_state:
    st.session_state.step_count = 0
if "waiting_for_tikitaka_choice" not in st.session_state:
    st.session_state.waiting_for_tikitaka_choice = False

# 5. 토론 주제 입력 영역
topic = st.text_input("아고라 채팅방에 던질 토론 주제를 입력하세요:", placeholder="예: 착한 사마리아인법을 국가가 법으로 강제해야 하는가?")

if st.button("💬 채팅방 입장 및 토론 시작"):
    if topic.strip():
        st.session_state.messages = []
        st.session_state.current_topic = topic
        st.session_state.discussion_active = True
        st.session_state.step_count = 0
        st.session_state.waiting_for_tikitaka_choice = False
        st.rerun()
    else:
        st.warning("토론 주제를 입력해 주세요.")

# 6. 카카오톡 대화방 화면 렌더링
if st.session_state.discussion_active:

    st.markdown(f'<div class="kakaotalk-notice">📌 [토론 주제] {st.session_state.current_topic}</div>', unsafe_allow_html=True)

    # 대화 출력
    for idx_msg, chat in enumerate(st.session_state.messages):
        if chat["type"] == "chat":
            lines = chat["lines"]
            speaker = chat["speaker"]
            icon = chat["icon"]
            color = chat["color"]
            time_str = chat["time"]
            
            st.markdown(f"""
            <div class="kakao-msg-row">
                <div class="kakao-avatar">{icon}</div>
                <div class="kakao-info-col">
                    <div class="kakao-sender" style="color: {color}; font-weight: bold;">{speaker}</div>
            """, unsafe_allow_html=True)
            
            for idx, line in enumerate(lines):
                is_last = (idx == len(lines) - 1)
                time_div = f'<div class="kakao-timestamp">{time_str}</div>' if is_last else ''
                
                colored_line = colorize_philosopher_names(line)
                
                st.markdown(f"""
                <div class="kakao-bubble-line">
                    <div class="kakao-bubble-box" style="border-left: 4px solid {color};">{colored_line}</div>
                    {time_div}
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("</div></div>", unsafe_allow_html=True)
            
        elif chat["type"] == "notice_card":
            st.markdown(f"""
            <div style="background-color: #FFFFFF; border-radius: 14px; margin: 10px 0 20px 52px; max-width: 340px; box-shadow: 0 1px 3px rgba(0,0,0,0.15); overflow: hidden; color: #111111;">
                <div style="padding: 16px 18px;">
                    <div style="font-weight: bold; margin-bottom: 8px; font-size: 0.95rem;">공지가 등록되었습니다.</div>
                    <div style="font-size: 0.9rem; color: #333333; margin-bottom: 12px;">철학자들의 티키타카 토론을 더 이어서 들으시겠습니까?</div>
                </div>
            """, unsafe_allow_html=True)
            
            with st.container():
                if st.button("📋 글 확인하기 (상단으로 이동)", key=f"go_to_notice_{idx_msg}", use_container_width=True):
                    st.markdown("""
                        <script>
                            const topElement = document.getElementById('top-anchor');
                            if (topElement) {
                                topElement.scrollIntoView({ behavior: 'smooth' });
                            }
                        </script>
                    """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
        elif chat["type"] == "summary":
            st.markdown(f"""
            <div class="summary-card">
                {chat['content'].replace('\n', '<br>')}
            </div>
            """, unsafe_allow_html=True)

    MAX_STEPS = 9  
    
    if st.session_state.waiting_for_tikitaka_choice:
        st.write("---")
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("🚀 이어서 티키타카 더 듣기", use_container_width=True):
                st.session_state.waiting_for_tikitaka_choice = False
                st.rerun()
        with col_b2:
            if st.button("📊 바로 사회자 요약으로 넘어가기", use_container_width=True):
                st.session_state.waiting_for_tikitaka_choice = False
                st.session_state.step_count = MAX_STEPS - 1
                st.rerun()

    elif st.session_state.step_count < MAX_STEPS:
        
        current_step = st.session_state.step_count
        now_time = datetime.now().strftime("%p %I:%M").replace("AM", "오전").replace("PM", "오후")
        
        if current_step == 0:
            spinner_msg = "🏛️ 철학자들이 입장해 첫 생각을 진중하게 발표하는 중..."
        elif current_step == MAX_STEPS - 1:
            spinner_msg = "📊 사회자가 대화 내용을 바탕으로 핵심 주장을 정리하는 중..."
        else:
            spinner_msg = f"🔥 톡으로 서로를 의식하며 티키타카 수다를 떠는 중... ({current_step}/{MAX_STEPS-2})"

        with st.spinner(spinner_msg):
            time.sleep(0.8)
            
            flat_history = []
            for m in st.session_state.messages:
                if m['type'] == 'chat':
                    flat_history.append(f"{m['speaker']}: {' '.join(m['lines'])}")

            # 1단계: 초반 입론
            if current_step == 0:
                for name, info in PHILOSOPHERS.items():
                    intro_content = (
                        f"{info['prompt']}\n\n"
                        f"[토론 주제] {st.session_state.current_topic}\n\n"
                        f"지침: 이 주제에 대한 너의 철학적 입장을 2~3문장으로 진중하게 밝혀라. 고등학생이 직관적으로 이해할 수 있는 쉬운 어휘를 써라."
                    )
                    try:
                        res = client.chat.completions.create(
                            model="gemini-3.5-flash-lite",
                            messages=[{"role": "user", "content": intro_content}],
                        )
                        text = res.choices[0].message.content.strip()
                        if not text:
                            continue
                    except Exception:
                        continue
                    
                    sentences = [s.strip() for s in text.replace('!', '!|').replace('?', '?|').replace('.', '.|').split('|') if s.strip()]
                    if not sentences:
                        continue

                    st.session_state.messages.append({
                        "type": "chat",
                        "speaker": name,
                        "icon": info["icon"],
                        "color": info["color"],
                        "lines": sentences,
                        "time": now_time
                    })
                
                st.session_state.step_count += 1
                st.rerun()

            # 난상토론 단계 (총 6번 반복)
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
                    debate_content = (
                        f"{info['prompt']}\n\n"
                        f"[토론 주제] {st.session_state.current_topic}\n\n"
                        f"[지금까지의 대화 흐름]\n" + ("\n".join(temp_history)) +
                        f"\n\n지침: 직전에 오간 대화 내용을 반드시 의식하고, '네'라는 호칭 대신 상대방의 이름(예: 소크라테스, 니체 등)을 자연스럽게 불러가며 1~2문장으로 날카롭게 반박해라."
                    )
                    try:
                        res = client.chat.completions.create(
                            model="gemini-3.5-flash-lite",
                            messages=[{"role": "user", "content": debate_content}],
                        )
                        text = res.choices[0].message.content.strip()
                        if not text:
                            continue
                    except Exception:
                        continue
                    
                    sentences = [s.strip() for s in text.replace('!', '!|').replace('?', '?|').replace('.', '.|').split('|') if s.strip()]
                    if not sentences:
                        continue

                    st.session_state.messages.append({
                        "type": "chat",
                        "speaker": name,
                        "icon": info["icon"],
                        "color": info["color"],
                        "lines": sentences,
                        "time": now_time
                    })
                    temp_history.append(f"{name}: {text}")

                st.session_state.step_count += 1
                
                if st.session_state.step_count >= 7:
                    st.session_state.messages.append({
                        "type": "notice_card"
                    })
                    st.session_state.waiting_for_tikitaka_choice = True

                st.rerun()

            # 사회자 최종 요약 카드 생성
            else:
                summary_prompt = (
                    f"토론 주제: {st.session_state.current_topic}\n"
                    f"지침: 사회자로서 이번 주제('{st.session_state.current_topic}')에 대해 니체, 소크라테스, 장자, 칸트, 홉스가 각각 어떤 고유한 관점과 주장을 펼칠지 고등학생 눈높이에 맞춰 마크다운 형식으로 작성해 주세요.\n"
                    "반드시 아래 형식으로만 작성하고, 각 철학자 이름 부분에 HTML 스타일 색상을 적용하여 가독성을 높여주세요:\n"
                    f"### 📊 [사회자] '{st.session_state.current_topic}'에 대한 철학자별 핵심 주장\n"
                    f"- **⚡ <span style='color: {PHILOSOPHERS['니체']['color']};'>니체</span>**: (주제에 맞는 니체 관점 1문장)\n"
                    f"- **🦉 <span style='color: {PHILOSOPHERS['소크라테스']['color']};'>소크라테스</span>**: (주제에 맞는 소크라테스 관점 1문장)\n"
                    f"- **🦋 <span style='color: {PHILOSOPHERS['장자']['color']};'>장자</span>**: (주제에 맞는 장자 관점 1문장)\n"
                    f"- **🕰️ <span style='color: {PHILOSOPHERS['칸트']['color']};'>칸트</span>**: (주제에 맞는 칸트 관점 1문장)\n"
                    f"- **🦁 <span style='color: {PHILOSOPHERS['홉스']['color']};'>홉스</span>**: (주제에 맞는 홉스 관점 1문장)"
                )
                try:
                    res = client.chat.completions.create(
                        model="gemini-3.5-flash-lite",
                        messages=[{"role": "user", "content": summary_prompt}],
                    )
                    summary_text = res.choices[0].message.content.strip()
                except Exception:
                    summary_text = (
                        f"### 📊 [사회자] '{st.session_state.current_topic}'에 대한 철학자별 핵심 주장\n"
                        f"- **⚡ <span style='color: {PHILOSOPHERS['니체']['color']};'>니체</span>**: 기존의 뻔한 틀을 깨부수고 스스로의 가치를 창조해야 한다.\n"
                        f"- **🦉 <span style='color: {PHILOSOPHERS['소크라테스']['color']};'>소크라테스</span>**: 네가 아는 것이 정말 진실인지 끊임없이 질문하고 무지를 깨달아야 한다.\n"
                        f"- **🦋 <span style='color: {PHILOSOPHERS['장자']['color']};'>장자</span>**: 억지로 무언가 하려 하지 말고 자연의 흐름에 그대로 몸을 맡겨야 한다.\n"
                        f"- **🕰️ <span style='color: {PHILOSOPHERS['칸트']['color']};'>칸트</span>**: 상황이 어떻든 보편적인 도덕 법칙과 의무를 엄격하게 지켜야 한다.\n"
                        f"- **🦁 <span style='color: {PHILOSOPHERS['홉스']['color']};'>홉스</span>**: 인간의 이기심을 통제하기 위해 강력한 사회적 질서와 법이 필수적이다."
                    )

                st.session_state.messages.append({
                    "type": "summary",
                    "content": summary_text
                })

            st.session_state.step_count += 1
            st.rerun()

    else:
        st.success("🎉 아고라 광장의 열띤 토론이 모두 종료되었습니다!")
        if st.button("🔄 새로운 주제로 대화하기"):
            st.session_state.messages = []
            st.session_state.discussion_active = False
            st.session_state.step_count = 0
            st.session_state.waiting_for_tikitaka_choice = False
            st.rerun()
