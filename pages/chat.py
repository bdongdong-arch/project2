import os
import random
import time
from datetime import datetime, timezone, timedelta
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

# 3. 5인 철학자 페르소나 정의 (고등학생 눈높이 및 성격 반영)
PHILOSOPHERS = {
    "니체": {
        "icon": "⚡",
        "color": "#D32F2F",
        "description": "기존 도덕을 비판하고 초인과 권력의 의지를 중시하는 사상가",
        "prompt": (
            "너는 독일의 철학자 프리드리히 니체다.\n"
            "[성격 및 말투 지침]\n"
            "- 고등학생이 이해하기 쉽게 쉬운 단어와 일상적인 비유를 써라.\n"
            "- 기존의 뻔한 도덕과 남의 시선에 갇히지 말고, 스스로 가치를 만들라고 당당하게 외쳐라.\n"
            "- 문장을 중간에 끊지 말고 완성된 2~3문장으로 답해라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    },
    "소크라테스": {
        "icon": "🦉",
        "color": "#1976D2",
        "description": "질문을 통해 자신의 무지를 겸손하게 탐구하는 철학자",
        "prompt": (
            "너는 고대 그리스의 철학자 소크라테스다.\n"
            "[성격 및 말투 지침]\n"
            "- 고등학생이 이해하기 쉽게 쉬운 단어와 일상적인 비유를 써라.\n"
            "- '그대', '친구여' 같은 호칭을 쓰며, 네가 아는 지식이 정말 진짜인지 부드럽게 반문해라.\n"
            "- 문장을 중간에 끊지 말고 완성된 2~3문장으로 답해라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    },
    "장자": {
        "icon": "🦋",
        "color": "#388E3C",
        "description": "자연의 흐름에 맡기고 억지로 하지 말라는 도인",
        "prompt": (
            "너는 고대 중국의 도가 철학자 장자(莊子)다.\n"
            "[대화 및 토론 지침]\n"
            "- 고등학생이 이해하기 쉽게 쉬운 단어와 일상적인 비유를 써라.\n"
            "- 아귀다툼하지 말고 자연의 흐름에 편안하게 몸을 맡기라고 사극 말투로 여유롭게 조언해라.\n"
            "- 전체 1~4문장으로 단호하게 답해라.\n"
            "- 반드시 순수 한국어로만 답변해라."
        )
    },
    "칸트": {
        "icon": "🕰️",
        "color": "#7B1FA2",
        "description": "정언명령과 보편적 도덕 법칙을 강조하는 18세기 독일의 철학자",
        "prompt": (
            "너는 18세기 독일의 철학자 이마누엘 칸트다.\n"
            "[성격 및 말투 지침]\n"
            "- 고등학생이 이해하기 쉽게 쉬운 단어와 일상적인 비유를 써라.\n"
            "- 감정이나 이익에 흔들리지 말고 누구나 지켜야 할 도덕 법칙과 원칙을 강조해라.\n"
            "- '그대'라는 호칭을 쓰며 전체 1~4문장으로 단호하게 결론을 내려라.\n"
            "- 반드시 순수 한국어로만 답변해라."
        )
    },
    "홉스": {
        "icon": "🦁",
        "color": "#E65100",
        "description": "강력한 국가와 법의 필요성을 주장하는 영국의 현실주의 철학자",
        "prompt": (
            "너는 영국의 철학자 토마스 홉스다.\n"
            "[성격 및 말투 지침]\n"
            "- 고등학생이 이해하기 쉽게 쉬운 단어와 일상적인 비유를 써라.\n"
            "- 법과 질서가 없으면 지옥 같은 싸움이 벌어지니 강력한 규칙이 필수라고 현실적으로 말해라.\n"
            "- 전체 1~4문장으로 단호하게 결론을 내려라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
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
topic = st.text_input("아고라 채팅방에 던질 토론 주제를 입력하세요:", placeholder="예: 동물원은 존재해야 하는가?")

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
        kst = timezone(timedelta(hours=9))
        now_time = datetime.now(kst).strftime("%p %I:%M").replace("AM", "오전").replace("PM", "오후")
        
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

            # 텍스트 정제 헬퍼 함수
            def clean_ai_text(text):
                import re
                text = re.sub(r'\[시스템 알림:[^\]]*\]', '', text)
                lines = [l.strip() for l in text.split('\n') if l.strip() and l.strip() != ']']
                return lines

            # 1단계: 초반 입론
            if current_step == 0:
                for name, info in PHILOSOPHERS.items():
                    intro_content = (
                        f"너는 {name}이다. {info['description']}\n\n"
                        f"[토론 주제] {st.session_state.current_topic}\n\n"
                        f"지침: 이 토론 주제에 대해 다른 사상가의 이름이나 주장을 언급하지 말고, 오직 너 자신의 철학적 관점에 입각해 고등학생이 이해하기 쉬운 쉬운 단어로 본인의 생각과 주장을 1~2문장으로 진중하게 밝혀라."
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
                    
                    cleaned_lines = clean_ai_text(text)
                    if not cleaned_lines:
                        continue

                    st.session_state.messages.append({
                        "type": "chat",
                        "speaker": name,
                        "icon": info["icon"],
                        "color": info["color"],
                        "lines": cleaned_lines[:2],
                        "time": now_time
                    })
                
                st.session_state.step_count += 1
                st.rerun()

            # 난상토론 단계
            elif current_step < MAX_STEPS - 1:
                recent_messages = [m for m in st.session_state.messages if m['type'] == 'chat']
                attacked_counts = {name: 0 for name in PHILOSOPHERS.keys()}
                
                for m in recent_messages[-4:]:
                    msg_text = " ".join(m['lines'])
                    for name in PHILOSOPHERS.keys():
                        if name in msg_text and m['speaker'] != name:
                            attacked_counts[name] += 1

                sorted_targets = sorted(attacked_counts.items(), key=lambda x: x[1], reverse=True)
                target_speaker = sorted_targets[0][0] if sorted_targets[0][1] > 0 else random.choice(list(PHILOSOPHERS.keys()))
                
                speakers_to_act = [target_speaker]
                other_philos = [n for n in PHILOSOPHERS.keys() if n != target_speaker]
                random.shuffle(other_philos)
                speakers_to_act.extend(other_philos[:random.randint(1, 2)])
                random.shuffle(speakers_to_act)

                temp_history = list(flat_history)
                for name in speakers_to_act:
                    info = PHILOSOPHERS[name]
                    
                    previous_statements = [m['lines'] for m in st.session_state.messages if m['type'] == 'chat' and m['speaker'] == name]
                    last_statement_str = " ".join(previous_statements[-1]) if previous_statements else "없음"

                    debate_content = (
                        f"{info['prompt']}\n\n"
                        f"[토론 주제] {st.session_state.current_topic}\n\n"
                        f"[지금까지의 대화 흐름]\n" + ("\n".join(temp_history)) +
                        f"\n\n[주의사항 - 절대 중복 금지 및 분량 제한]: 네가 직전에 한 말: \"{last_statement_str}\"\n"
                        f"지침: 고등학생이 이해하기 쉬운 단어로, 상대방의 주장에 대해 일부분 수용하면서도 본인의 철학으로 예리하게 반박해라. **반드시 문장을 끝까지 완성하여 2~3줄(2~3문장 이내)로** 간결하게 작성해라."
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
                    
                    cleaned_lines = clean_ai_text(text)
                    if not cleaned_lines:
                        continue

                    cleaned_lines = cleaned_lines[:3]

                    st.session_state.messages.append({
                        "type": "chat",
                        "speaker": name,
                        "icon": info["icon"],
                        "color": info["color"],
                        "lines": cleaned_lines,
                        "time": now_time
                    })
                    temp_history.append(f"{name}: {' '.join(cleaned_lines)}")

                st.session_state.step_count += 1
                
                if st.session_state.step_count >= 7:
                    st.session_state.waiting_for_tikitaka_choice = True

                st.rerun()

            # 사회자 최종 요약 카드 생성 (마크다운 ** 기호가 깨지지 않도록 깔끔하게 수정)
            else:
                summary_prompt = (
                    f"토론 주제: {st.session_state.current_topic}\n"
                    f"지침: 사회자로서 이번 주제('{st.session_state.current_topic}')에 대해 니체, 소크라테스, 장자, 칸트, 홉스가 각각 어떤 고유한 관점과 주장을 펼쳤는지 고등학생 눈높이에 맞춰서 1문장씩 요약해 주세요.\n"
                    "출력 시 철학자 이름 앞뒤에 마크다운 기호(**)를 절대 붙이지 말고, 순수 텍스트와 HTML 태그만 사용해 주세요.\n"
                    "반드시 아래 형식으로만 작성해 주세요:\n"
                    f"### 📊 [사회자] '{st.session_state.current_topic}'에 대한 철학자별 핵심 주장\n"
                    f"- ⚡ 니체: (주제에 맞는 니체 관점 1문장)\n"
                    f"- 🦉 소크라테스: (주제에 맞는 소크라테스 관점 1문장)\n"
                    f"- 🦋 장자: (주제에 맞는 장자 관점 1문장)\n"
                    f"- 🕰️ 칸트: (주제에 맞는 칸트 관점 1문장)\n"
                    f"- 🦁 홉스: (주제에 맞는 홉스 관점 1문장)"
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
                        f"- ⚡ 니체: 기존의 틀을 깨부수고 스스로의 가치를 창조해야 한다.\n"
                        f"- 🦉 소크라테스: 네가 아는 것이 정말 진실인지 끊임없이 질문해야 한다.\n"
                        f"- 🦋 장자: 억지로 무언가 하려 하지 말고 자연의 흐름에 몸을 맡겨야 한다.\n"
                        f"- 🕰️ 칸트: 어떤 상황에서도 보편적인 도덕 법칙과 의무를 지켜야 한다.\n"
                        f"- 🦁 홉스: 인간의 이기심을 통제하기 위해 강력한 법과 질서가 필수적이다."
                    )

                # 요약 텍스트 내부의 철학자 이름에 고유 색상 입히기
                summary_text = colorize_philosopher_names(summary_text)

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
