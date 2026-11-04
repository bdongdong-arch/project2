import os
import random
import time
import re
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

# 3. 5인 철학자 페르소나 정의
PHILOSOPHERS = {
    "니체": {
        "icon": "⚡",
        "color": "#D32F2F",
        "description": "기존 도덕을 비판하고 초인과 권력의 의지를 중시하는 사상가",
        "prompt": (
            "너는 독일의 철학자 프리드리히 니체다.\n"
            "[성격 및 말투 지침]\n"
            "- 실제 삶에서는 예의 바르고 온화하며 섬세한 감수성을 지녔고, 음악과 자연을 사랑하며 조용하고 고독을 즐겼다.\n"
            "- 평소에는 차분하고 정중하며 상대에게 결례를 범하지 않는 태도를 보이며, 공격적이거나 거친 인물이 아니다.\n"
            "- 그러나 철학적 문제를 다룰 때에는 기존의 도덕, 종교, 사회적 가치가 당연하게 받아들여지는 것을 비판하며, 스스로 가치를 창조하고 자신을 극복하는 '초인'과 '권력의 의지'를 중시한다.\n"
            "- 상대의 의견을 존중하면서도 그 사람이 당연하게 받아들이는 전제를 부드러운 태도 속에 조용하고 날카로운 질문과 사색적인 반론으로 파고들어라.\n"
            "- 고등학생이 이해하기 쉬운 어휘를 사용해라.\n"
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
            "- 세속적 부나 명예에 연연하지 않고 소탈하게 살아가며, 자신의 무지를 겸손하게 인정하는 태도를 지녔다.\n"
            "- 자신이 모든 것을 알고 있다고 주장하기보다 대화를 통해 함께 진리를 탐구하며, 상대에게 생각을 강요하지 않는다.\n"
            "- 고풍스럽고 차분한 분위기를 지니며, '그대'나 '친구여' 같은 호칭을 쓰고 '~하는가', '~일세', '~하지 않겠는가' 같은 표현을 자연스럽게 사용하라.\n"
            "- 질문을 많이 던지되 공격적이거나 권위적이지 않으며, 하나의 질문에서 또 다른 질문을 만들어 상대의 생각을 깊이 파고들어라.\n"
            "- 고등학생이 이해하기 쉬운 어휘를 사용해라.\n"
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
            "- 하시오, 합니까 같은 사극 말투로 말하고 혼잣말이나 쓸데없는 질문을 자주 던지지 마라.\n"
            "- 인간이 만든 인위적인 시비선악, 세속적 가치나 규범의 부질없음을 지적하고, 자연의 흐름에 맡기는 '무위자연(無爲自然)'과 만물이 하나라는 '물아일체' 관점에서 논제에 답해라.\n"
            "- 얽매이지 않고 여유로우면서도 뼈가 있는 비유와 해학을 담아 단호하게 자신의 사상을 밝혀라.\n"
            "- 고등학생이 이해하기 쉬운 어휘를 사용해라.\n"
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
            "- 철저한 규칙성과 신중함을 지니고 있어 생활을 규칙적으로 관리하며 예상치 못한 변화를 불편해하고, 결정을 내릴 때도 충분히 깊이 생각한다.\n"
            "- 그러나 이러한 엄격함과 달리 실제 인간관계에서는 친절하고 사교적이며 대화를 즐기고 건조한 유머를 구사한다.\n"
            "- 철학적·도덕적 문제를 다룰 때에는 매우 엄격하고 논리적인 태도로 돌변하여, 감정이나 이익보다 '정언명령'과 보편적 도덕 법칙, 인간을 수단이 아닌 목적으로 대하는 원칙을 강조한다.\n"
            "- '그대', '~하지 않겠습니까' 등의 품위 있는 존댓말을 쓰며 대화해라.\n"
            "- 고등학생이 이해하기 쉬운 어휘를 사용해라.\n"
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
            "- 고집스럽고 완고하며, 인간을 자기보존과 이익을 추구하는 이기적인 존재로 바라보는 현실주의자다.\n"
            "- 자연 상태의 '만인의 만인에 대한 투쟁'과 강력한 국가(리바이어던)의 필요성을 냉철하고 직설적인 어조로 주장한다.\n"
            "- 감정에 흔들리지 않고 '그것은 지나치게 낙관적인 생각입니다', '그러므로 ~해야 합니다'처럼 냉철하고 직설적이며 권위 있고 단호한 결론을 내려라.\n"
            "- 고등학생이 이해하기 쉬운 어휘를 사용해라.\n"
            "- 반드시 순수 한국어로만 답해라."
        )
    }
}

# 텍스트 내 철학자 이름 색상 적용 및 **기호를 볼딕체(<b>)로 변환해 주는 헬퍼 함수
def colorize_philosopher_names(text):
    # 1. **문구** 형태를 HTML <b> 태그로 변환
    text = re.sub(r'\*\*(.*?)\*\*', r'<b style="font-weight: bold;">\1</b>', text)
    
    # 2. 철학자 이름 색상 적용
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
topic = st.text_input("아고라 채팅방에 던질 토론 주제를 입력하세요:", placeholder="예: 동물원은 존재해야 하는가?", key="topic_input")

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
            def clean_ai_text(text, max_sentences=2):
                text = re.sub(r'\[시스템 알림:[^\]]*\]', '', text)
                raw_lines = text.split('\n')
                sentences = []
                for rl in raw_lines:
                    rl = rl.strip()
                    if not rl or rl == ']':
                        continue
                    split_sents = [s.strip() for s in re.split(r'(?<=[.?!])\s+', rl) if s.strip()]
                    if split_sents:
                        sentences.extend(split_sents)
                    else:
                        sentences.append(rl)
                return sentences[:max_sentences]

            # 1단계: 초반 입론 (다른 사람 이름 호명 금지, 오직 자기 본인의 주장만 말함)
            if current_step == 0:
                for name, info in PHILOSOPHERS.items():
                    intro_content = (
                        f"{info['prompt']}\n\n"
                        f"[토론 주제] {st.session_state.current_topic}\n\n"
                        f"지침: 이 토론 주제에 대해 다른 어떤 사상가의 이름이나 호칭(그대, 친구 등)도 언급하지 마라! 오직 너 자신({name})의 철학적 관점에만 입각해 고등학생이 이해하기 쉬운 어휘로 **딱 1~2문장**만 밝혀라. 토론 주제에 대한 **본인의 최종 주장 및 결론 부분은 반드시 굵은 글씨(`**결론**`)로 강조**해서 작성해라."
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
                    
                    cleaned_lines = clean_ai_text(text, max_sentences=2)
                    if not cleaned_lines:
                        continue

                    st.session_state.messages.append({
                        "type": "chat",
                        "speaker": name,
                        "icon": info["icon"],
                        "color": info["color"],
                        "lines": cleaned_lines,
                        "time": now_time
                    })
                
                st.session_state.step_count += 1
                st.rerun()

            # 난상토론 단계 (철학자들 서로의 이름을 호명하며 반박)
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
                
                attackers = []
                for m in recent_messages[-3:]:
                    msg_text = " ".join(m['lines'])
                    if target_speaker in msg_text and m['speaker'] != target_speaker:
                        if m['speaker'] not in attackers:
                            attackers.append(m['speaker'])
                
                if not attackers:
                    other_philos = [n for n in PHILOSOPHERS.keys() if n != target_speaker]
                    attackers = [random.choice(other_philos)]

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

                    if name == target_speaker and len(attackers) > 1:
                        for atk in attackers[:2]:
                            individual_debate_content = (
                                f"{info['prompt']}\n\n"
                                f"[토론 주제] {st.session_state.current_topic}\n\n"
                                f"[지금까지의 대화 흐름]\n" + ("\n".join(temp_history)) +
                                f"\n\n[주의사항 - 개별 반박]: {atk}의 최근 주장에 대해, {name}로서 반드시 **상대방 철학자({atk})의 이름을 부르며** 짧게 1~2문장으로 반박해라."
                            )
                            try:
                                res = client.chat.completions.create(
                                    model="gemini-3.5-flash-lite",
                                    messages=[{"role": "user", "content": individual_debate_content}],
                                )
                                text = res.choices[0].message.content.strip()
                                if not text:
                                    continue
                            except Exception:
                                continue

                            cleaned_lines = clean_ai_text(text, max_sentences=2)
                            if not cleaned_lines:
                                continue

                            st.session_state.messages.append({
                                "type": "chat",
                                "speaker": name,
                                "icon": info["icon"],
                                "color": info["color"],
                                "lines": cleaned_lines,
                                "time": now_time
                            })
                            temp_history.append(f"{name}: {' '.join(cleaned_lines)}")
                    else:
                        target_to_mention = random.choice([n for n in PHILOSOPHERS.keys() if n != name])
                        debate_content = (
                            f"{info['prompt']}\n\n"
                            f"[토론 주제] {st.session_state.current_topic}\n\n"
                            f"[지금까지의 대화 흐름]\n" + ("\n".join(temp_history)) +
                            f"\n\n[주의사항 - 상대방 호명 반박]: 네가 직전에 한 말: \"{last_statement_str}\"\n"
                            f"지침: 고등학생이 이해하기 쉬운 어휘로, 뻔한 말을 반복하지 말고 반박해라. 말할 때 **반드시 다른 철학자 중 1명의 이름(예: {target_to_mention})을 직접 호명하며** 1~2문장으로 아주 짧고 간결하게 대답해라."
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
                        
                        cleaned_lines = clean_ai_text(text, max_sentences=2)
                        if not cleaned_lines:
                            continue

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

            # 사회자 최종 요약 카드 생성
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
            st.session_state.topic_input = ""
            st.rerun()
