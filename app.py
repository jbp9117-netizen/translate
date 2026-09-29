import logging

import streamlit as st

from translator import LANGUAGES, TranslationError, get_model, translate

MAX_CHARS = 2000
# 국기 이모지는 Windows에서 글자(US, JP…)로 보이므로 모든 환경에서 같은 모양인 텍스트 배지를 쓴다
BADGES = {
    "english": "EN",
    "japanese": "JA",
    "vietnamese": "VI",
    "north_korean": "NK",
}
HIGHLIGHT_KEY = "north_korean"  # 앱의 핵심 기능이라 카드를 강조한다

# 색은 반투명 값만 사용해 라이트/다크 테마 배경 모두에 어울리게 한다.
CSS = """
<style>
[class*="st-key-card_"] pre,
[class*="st-key-card_"] code {
    font-family: inherit !important;
    font-size: 1.05rem !important;
    line-height: 1.65 !important;
}
[class*="st-key-card_"] { min-height: 140px; }
.st-key-card_HIGHLIGHT {
    border-color: rgba(229, 72, 77, 0.65) !important;
    background: rgba(229, 72, 77, 0.06);
}
.card-title { font-weight: 600; font-size: 1.05rem; margin: 0; }
.lang-badge {
    display: inline-block;
    min-width: 2.2em;
    margin-right: 0.4em;
    padding: 0.05em 0.45em;
    border-radius: 0.4em;
    background: rgba(128, 128, 128, 0.18);
    font-size: 0.8em;
    font-weight: 700;
    text-align: center;
    letter-spacing: 0.03em;
}
.st-key-card_HIGHLIGHT .lang-badge { background: rgba(229, 72, 77, 0.22); }
/* 한국어가 단어 중간에서 줄바꿈되지 않게 */
.stApp h1, .stApp p { word-break: keep-all; }
</style>
""".replace("HIGHLIGHT", HIGHLIGHT_KEY)


@st.cache_data(ttl=3600, max_entries=100, show_spinner=False)
def cached_translate(text: str, languages: tuple[str, ...], model: str) -> dict:
    # 같은 입력을 다시 번역하거나, 번역 중 버튼을 한 번 더 눌러 화면이 다시 실행돼도
    # API를 중복 호출하지 않는다. model은 .env 변경 시 캐시를 구분하기 위한 키로만 쓴다.
    return translate(text, list(languages))


st.set_page_config(page_title="AI 다국어 번역기", page_icon="🌏", layout="centered")
st.markdown(CSS, unsafe_allow_html=True)

st.title("🌏 AI 다국어 번역기")
st.caption("한 번 입력하면 영어 · 일본어 · 베트남어 · 북한 사투리로 동시에 번역해 드립니다.")

with st.form("translate_form", border=False):
    text = st.text_area(
        "번역할 텍스트",
        height=150,
        max_chars=MAX_CHARS,
        placeholder="예) 오늘 저녁에 같이 밥 먹을래?",
        help="Ctrl+Enter로도 번역할 수 있습니다.",
    )
    languages = st.pills(
        "번역할 언어",
        options=list(LANGUAGES),
        selection_mode="multi",
        default=list(LANGUAGES),
        format_func=LANGUAGES.get,
    )
    submitted = st.form_submit_button("번역하기", type="primary", width="stretch")

if submitted:
    st.session_state.result = None
    st.session_state.error = None
    if not text.strip():
        st.session_state.error = ("warning", "번역할 텍스트를 입력해주세요.")
    elif not languages:
        st.session_state.error = ("warning", "번역할 언어를 하나 이상 선택해주세요.")
    else:
        try:
            with st.spinner("번역 중입니다... (긴 글은 최대 1분 정도 걸릴 수 있습니다)"):
                st.session_state.result = cached_translate(text, tuple(languages), get_model())
        except TranslationError as e:
            st.session_state.error = ("error", str(e))
        except Exception:
            # 예상하지 못한 오류도 화면에 스택트레이스 대신 안내 문구만 보여준다
            logging.exception("unexpected translation failure")
            st.session_state.error = ("error", "알 수 없는 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")

result = st.session_state.get("result")
error = st.session_state.get("error")

if error:
    level, message = error
    getattr(st, level)(message)

if result:
    keys = [k for k in LANGUAGES if k in result]
    for i in range(0, len(keys), 2):
        for col, key in zip(st.columns(2), keys[i:i + 2]):
            with col, st.container(border=True, key=f"card_{key}"):
                st.markdown(
                    f'<p class="card-title"><span class="lang-badge">{BADGES[key]}</span>'
                    f"{LANGUAGES[key]}</p>",
                    unsafe_allow_html=True,
                )
                # st.code는 텍스트를 이스케이프해 표시하고 복사 버튼을 제공한다
                st.code(result[key], language=None, wrap_lines=True)
elif not error:
    st.info("텍스트를 입력하고 **번역하기**를 누르면 이곳에 번역 결과가 표시됩니다.")
