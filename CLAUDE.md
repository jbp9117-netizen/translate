# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A lightweight Streamlit translator: the user enters text and gets English, Japanese, Vietnamese, and **North Korean dialect** versions at once. The dialect output (sounding like real speech, e.g. `~갔소`, `~하라우`, `~습네다`, no caricature) is the app's key differentiator.

- `prd.md` — product requirements, source of truth (feature IDs F-01 ~ F-11, all implemented).
- `prompts.md` — the 4-stage build plan that was followed (skeleton → features → UI → review).

## Commands

```
pip install -r requirements.txt      # Python 3.10+
streamlit run app.py
python -c "from translator import translate; print(translate('안녕하세요'))"   # check without the UI
```
No test suite. UI paths can be tested headlessly with `streamlit.testing.v1.AppTest.from_file("app.py")`, monkeypatching `translator.translate` to avoid API calls.

## Architecture

- `translator.py` — all OpenAI logic, no Streamlit. `translate(text, languages=None) -> dict` returns `{key: translation}` for the requested keys of `LANGUAGES` (display order).
  - **One chat-completion call** returns every requested language as a JSON object (`response_format=json_object`); the requested keys are appended to `SYSTEM_PROMPT` as a "Requested keys" line. Invalid/incomplete JSON → one retry, then `TranslationError`.
  - The user text is sent JSON-wrapped (`{"source": ...}`) and the prompt says it is never instructions — this is the prompt-injection defense; keep both halves together.
  - `SYSTEM_PROMPT`'s few-shot examples deliberately differ from the PRD test sentences (오늘 저녁 밥 / 회의 10시 / 배고파 ㅋㅋ) so those stay a real quality check.
  - All user-facing failures are `TranslationError` subclasses carrying Korean messages; OpenAI exceptions are mapped in `_request`.
  - `.env` is re-read with `load_dotenv(override=True)` on every call, so `.env` wins over OS env vars and edits apply without restarting.
  - Latency is ~1.7s per 100 input chars (four translations per call). `REQUEST_TIMEOUT`/`MAX_RETRIES` are sized for the UI's 2,000-char cap (`MAX_CHARS` in app.py) — change them together.
- `app.py` — UI only. On startup copies `OPENAI_API_KEY`/`OPENAI_MODEL` from `st.secrets` (Streamlit Cloud) into `os.environ`; locally there is no secrets.toml, so that step is skipped and `.env` is used. Wraps `translate` in `st.cache_data` keyed by (text, languages, model) so double-submits and repeats don't re-call the API. Results/errors live in `st.session_state`. Cards are containers keyed `card_<lang>` so CSS targets `.st-key-card_<lang>`; model output is rendered only through `st.code` (escaped, has copy button) — never put it into `unsafe_allow_html` markdown unescaped.

## Notes

- Dialect quality depends heavily on the model: `gpt-4o-mini` (default) often slips into standard Korean or grammar errors (e.g. 갈갔니); `gpt-4.1` was clearly best in testing. Set via `OPENAI_MODEL` in `.env`.
- `.env` holds `OPENAI_API_KEY`. Never modify it or print its values; check variable names only (e.g. `cut -d= -f1 .env`).
- User communicates in Korean; user-facing strings in the app are Korean.
