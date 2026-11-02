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

# 3. 5인 철학자 페르소나 정의 (대화 시 상대방 이름을 적극적으로 호명하도록 지침 추가)
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
            "- ** 대화할 때 상대방 철학자(소크라테스, 장자, 칸트, 홉스 중 한 명)의 이름을 직접 부르며(호명하며) 대화해라.**\n"
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
            "- **반드시 대화할 때 상대방 철학자(니체, 장자, 칸트, 홉스 중 한 명)의 이름을 직접 부르며(호명하며) 대화해라.**\n"
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
