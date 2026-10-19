
import os
from openai import OpenAI
import streamlit as st

# 페이지 기본 설정
st.set_page_config(page_title="🏛️ AI 철학자 아고라 토론장", page_icon="🏛️")

st.title("🏛️ 고대 아고라 철학자 토론장")
st.write("토론 주제를 입력하면 5명의 철학자가 아고라 광장에서처럼 서로 대화를 주고받으며 토론을 펼칩니다.")

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

# 3. 5인 철학자 페르소나 및 대화 스타일 정의
PHILOSOPHERS = {
    "니체": {
        "icon": "⚡",
        "description": "기존 도덕을 해체하고 스스로 가치를 창조하라는 사상가",
        "prompt": (
            "너는 프레드리히 니체다.\n"
            "- 정중하고 예의 바른 태도를 유지하되, 기존 도덕과 사회적 관습을 날카롭게 파고들어 비판해라.\n"
            "- 실제 메신저나 사람과 직접 대화하듯 편안한 구어체(~해요, ~죠, ~잖아요)를 사용해라.\n"
            "- 단호하게 끊지 말고 타인의 의견에 반응하며 유연하게 생각을 건네라.\n"
            "- 줄바꿈 포함 2~3문장 이내로 자연스럽게 말해라.\n"
            "- 반드시 한국어로만 답해라."
        )
    },
    "소크라테스": {
        "icon": "🦉",
        "description": "무지의 자각을 이끌고 진리를 탐구하는 소탈한 철학자",
        "prompt": (
            "너는 소크라테스다.\n"
            "- '그대'나 '친구여' 같은 표현을 쓰며 친근하게 대화해라.\n"
            "- 상대를 훈계하거나 일방적으로 결론 내리지 말고, 가벼운 반문과 질문을 던지며 진리를 함께 찾아가라.\n"
            "- 실제 사람과 수다 떨듯 편안하고 자연스러운 구어체를 유지해라.\n"
            "- 줄바꿈 포함 2~3문장 이내로 답해라.\n"
            "- 반드시 한국어로만 답해라."
        )
    },
    "장자": {
        "icon": "🦋",
        "description": "무위자연과 물아일체로 세속의 굴레를 비워주는 도인",
        "prompt": (
            "너는 장자(莊子)다.\n"
            "- 세속적 시비선악에 연연하지 않고 허허 웃으며 받아치는 유유자적한 어조를 써라.\n"
            "- 사극 말투나 고어체 대신 편안한 대화체(~지요, ~군요)와 가벼운 비유로 상대의 긴장을 풀어주어라.\n"
            "- 실제 대화하듯 2~3문장 이내로 자연스럽게 답해라.\n"
            "- 반드시 한국어로만 답해라."
        )
    },
    "칸트": {
        "icon": "🕰️",
        "description": "보편적 도덕 법칙과 정언명령을 강조하는 원칙주의자",
        "prompt": (
            "너는 이마누엘 칸트다.\n"
            "- 평소엔 친절하고 사교적이지만, 도덕과 규칙 이야기가 나오면 보편적 원칙과 의무를 강조해라.\n"
            "- 논문 같은 말투 대신 품위 있고 정중한 존댓말(~습니다, ~입니다)을 써서 실제 대화하듯 말해라.\n"
            "- 줄바꿈 포함 2~3문장 이내로 깔끔하게 답해라.\n"
            "- 반드시 한국어로만 답해라."
        )
    },
    "홉스": {
        "icon": "🦁",
        "description": "만인의 만인에 대한 투쟁과 강력한 국가를 주장하는 현실주의자",
        "prompt": (
            "너는 토마스 홉스다.\n"
            "- 인간의 이기적인 본성을 바탕으로 낙관적인 주장에 대해 현실을 짚어주어라.\n"
            "- 교과서적 설명 대신, 메신저에서 대화하듯 툭툭 현실적인 의견을 건네라.\n"
            "- 줄바꿈 포함 2~3문장 이내로 단호하면서도 자연스럽게 답해라.\n"
            "- 반드시 한국어로만 답해라."
        )
    }
}

# 4. 토론 상태 관리
if "discussion_history" not in st.session_state:
    st.session_state.discussion_history = []

# 5. 토론 주제 입력
topic = st.text_input("아고라 광장에 던질 토론 주제를 입력하세요:", placeholder="예: 착한 사마리아인법을 국가가 법으로 강제해야 하는가?")

if st.button("🏛️ 토론 시작하기"):
    if topic.strip():
        # 기존 기록 초기화 및 주제 저장
        st.session_state.discussion_history = [{"role": "user", "content": f"[토론 주제] {topic}"}]
        
        st.subheader(f"💬 주제: {topic}")
        
        # 전체 대화 맥락을 누적할 리스트
        discussion_context = []
        
        # 5명의 철학자가 순서대로 한 번씩 대화 진행
        for name, info in PHILOSOPHERS.items():
            with st.chat_message("assistant", avatar=info["icon"]):
                st.markdown(f"**{info['icon']} {name}**")
                
                # 프롬프트 구성: 기존 대화 내역 + 지금까지 다른 철학자들이 한 말
                prompt_content = f"{info['prompt']}\n\n[현재 토론 주제]\n{topic}\n\n[지금까지 아고라 광장에서 오간 대화 내역]\n"
                for msg in discussion_context:
                    prompt_content += f"{msg['speaker']}: {msg['text']}\n"
                
                prompt_content += f"\n위 맥락을 바탕으로, {name}의 사상과 성격을 살려 앞사람들의 이야기에 자연스럽게 이어지도록 실제 사람처럼 답해라."

                messages_to_send = [
                    {"role": "system", "content": prompt_content},
                    {"role": "user", "content": "너의 생각을 말해다오."}
                ]

                try:
                    # Gemini API 호출 (스트리밍)
                    response_stream = client.chat.completions.create(
                        model="gemini-3.5-flash-lite",
                        messages=messages_to_send,
                        stream=True,
                    )
                    
                    full_response = st.write_stream(response_stream)
                    
                    # 맥락 누적
                    discussion_context.append({"speaker": name, "text": full_response})
                    st.session_state.discussion_history.append({"speaker": name, "icon": info["icon"], "content": full_response})
                    
                except Exception as e:
                    st.write("답변을 불러오는 중 오류가 발생했습니다.")
    else:
        st.warning("토론 주제를 입력해 주세요.")

# 이전 토론 내역이 있을 경우 표시
elif st.session_state.discussion_history:
    st.subheader("💬 진행된 토론 내용")
    for item in st.session_state.discussion_history:
        if "role" in item and item["role"] == "user":
            st.info(item["content"])
        else:
            with st.chat_message("assistant", avatar=item["icon"]):
                st.markdown(f"**{item['icon']} {item['speaker']}**")
                st.write(item["content"])
