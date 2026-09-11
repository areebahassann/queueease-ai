"""
QueueEase AI — Virtual Queue & Guidance Assistant
Hackathon prototype (Streamlit)

Flow:
 1. Conversational Intake      -> user types request in English/Urdu/Roman Urdu
 2. AI Request Classification  -> Claude API (if key set) + keyword fallback
 3. AI Document Checklist      -> generated / grounded on services_data.py
 4. Virtual Token + Wait Time  -> simulated live queue stored in session_state
 5. Smart Notification         -> simulated "your turn is approaching" message
"""

import os
import json
import time
import random
from datetime import datetime, timedelta

import streamlit as st
from services_data import SERVICES, keyword_match

# ---------------------------------------------------------------------------
# Optional: Anthropic API (Generative AI core). Falls back gracefully to a
# rule-based engine if no API key is configured, so the demo NEVER breaks
# during a live presentation or recording.
# ---------------------------------------------------------------------------
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
USE_AI = bool(ANTHROPIC_API_KEY)

if USE_AI:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    except Exception:
        USE_AI = False


def ai_classify_and_summarize(user_text: str, matched_service: dict) -> dict:
    """
    Calls Claude to (a) confirm classification in a friendly way and
    (b) write a short, warm, bilingual (Urdu/Roman Urdu + English) summary
    of next steps. Grounded strictly in the matched_service data so the
    model cannot invent documents that aren't verified.
    """
    fallback = {
        "friendly_summary": (
            f"Aapki request '{user_text}' ke liye humne '{matched_service['service']}' "
            f"({matched_service['institution']} — {matched_service['department']}) "
            f"identify kiya hai. Neeche di gayi checklist ke mutabiq documents sath le jayein."
        )
    }
    if not USE_AI:
        return fallback

    prompt = f"""You are QueueEase AI, a warm and clear virtual assistant for Pakistani
government/hospital service visitors. A citizen wrote this request (may be English,
Urdu, or Roman Urdu):

"{user_text}"

It has been classified as:
Institution: {matched_service['institution']}
Department: {matched_service['department']}
Service: {matched_service['service']}
Required documents: {', '.join(matched_service['documents'])}

Write a short (3-4 sentences), warm, reassuring confirmation message in simple
Roman Urdu mixed with English (the way people actually text in Pakistan),
confirming what they need and telling them to check the checklist below.
Do not invent any documents beyond what is listed above. Return plain text only."""

    try:
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(b.text for b in resp.content if hasattr(b, "text"))
        return {"friendly_summary": text.strip() or fallback["friendly_summary"]}
    except Exception:
        return fallback


# ---------------------------------------------------------------------------
# Simulated live queue database (would be a Google Sheet / real DB in prod)
# ---------------------------------------------------------------------------
def init_queue_state():
    if "queue" not in st.session_state:
        # queue: {service_id: [ {token, issued_at}, ... ]}
        st.session_state.queue = {svc["id"]: [] for svc in SERVICES}
    if "my_tokens" not in st.session_state:
        st.session_state.my_tokens = []


def issue_token(service: dict) -> dict:
    queue = st.session_state.queue[service["id"]]
    token_no = f"{service['id'][:3].upper()}-{len(queue) + 1:03d}"
    people_ahead = len(queue)
    entry = {
        "token": token_no,
        "issued_at": datetime.now(),
        "people_ahead": people_ahead,
    }
    queue.append(entry)
    est_wait_min = people_ahead * service["avg_service_time_min"] + random.randint(1, 4)
    entry["estimated_wait_min"] = est_wait_min
    entry["estimated_time"] = datetime.now() + timedelta(minutes=est_wait_min)
    st.session_state.my_tokens.append({**entry, "service": service})
    return entry


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.set_page_config(page_title="QueueEase AI", page_icon="🎫", layout="centered")
init_queue_state()

st.title("🎫 QueueEase AI")
st.caption("Ghar baithe apni line lagayein — AI-powered virtual queue & guidance assistant")

if not USE_AI:
    st.info(
        "ℹ️ Demo mode: ANTHROPIC_API_KEY set nahi hai, isliye smart rule-based engine "
        "use ho rahi hai. Full Generative AI responses ke liye Space Secrets mein "
        "ANTHROPIC_API_KEY add karein.",
        icon="🤖",
    )

tab1, tab2 = st.tabs(["📝 New Request", "🔔 Mera Token / Status"])

# ---------------- TAB 1: New request ----------------
with tab1:
    st.subheader("Aapko kya chahiye?")
    st.write("Apni zaban mein likhein — English, Urdu ya Roman Urdu, sab chalega.")

    example_col1, example_col2, example_col3 = st.columns(3)
    examples = [
        "mujhe apna domicile banwana hai",
        "I need to renew my father's CNIC",
        "dil ka doctor dikhana hai"
    ]
    chosen_example = None
    for col, ex in zip([example_col1, example_col2, example_col3], examples):
        if col.button(ex, use_container_width=True):
            chosen_example = ex

    user_text = st.text_area(
        "Apni request likhein:",
        value=chosen_example or "",
        placeholder="e.g. mujhe naya shanakhti card banwana hai...",
        height=90,
    )

    if st.button("🔍 Submit & Get Guidance", type="primary", use_container_width=True):
        if not user_text.strip():
            st.warning("Pehle apni request likhein.")
        else:
            with st.spinner("AI aapki request samajh rahi hai..."):
                matched = keyword_match(user_text)
                time.sleep(0.6)  # small UX pause

            if not matched:
                st.error(
                    "Maazrat, hum aapki request classify nahi kar sakay. Zara mazeed "
                    "tafseel ke sath dobara likhein (e.g. 'CNIC renewal', 'domicile', "
                    "'cardiology doctor')."
                )
            else:
                ai_out = ai_classify_and_summarize(user_text, matched)

                st.success(f"✅ Classified as: **{matched['service']}**")
                st.markdown(f"**Institution:** {matched['institution']}  \n"
                            f"**Department:** {matched['department']}")
                st.write(ai_out["friendly_summary"])

                st.markdown("#### 📋 Document Checklist")
                for doc in matched["documents"]:
                    st.checkbox(doc, key=f"doc_{matched['id']}_{doc}")
                st.caption(f"💰 {matched['fee_note']}")

                st.markdown("#### 🎟️ Virtual Token")
                entry = issue_token(matched)
                c1, c2, c3 = st.columns(3)
                c1.metric("Token No.", entry["token"])
                c2.metric("People Ahead", entry["people_ahead"])
                c3.metric("Est. Wait", f"{entry['estimated_wait_min']} min")
                st.info(
                    f"📅 Estimated turn: **{entry['estimated_time'].strftime('%I:%M %p')}**. "
                    f"'Mera Token / Status' tab mein check karte rahein.",
                    icon="⏰",
                )

# ---------------- TAB 2: Status ----------------
with tab2:
    st.subheader("Aapke Tokens")
    if not st.session_state.my_tokens:
        st.write("Abhi tak koi token issue nahi hua. 'New Request' tab se shuru karein.")
    else:
        for t in reversed(st.session_state.my_tokens):
            elapsed = (datetime.now() - t["issued_at"]).total_seconds() / 60
            remaining = max(0, round(t["estimated_wait_min"] - elapsed))
            with st.container(border=True):
                st.markdown(f"**{t['token']}** — {t['service']['service']} "
                            f"({t['service']['institution']})")
                if remaining <= 2:
                    st.warning(
                        f"🔔 Aapki baari {max(remaining,0)} minute mein aa sakti hai — "
                        f"please pohnch jayein!",
                        icon="🔔",
                    )
                else:
                    st.write(f"⏳ Estimated remaining wait: **{remaining} min**")

st.divider()
st.caption(
    "QueueEase AI — Hackathon Prototype · Built with Streamlit + Claude API · "
    "Free & open-source demo. Not affiliated with NADRA or any government body."
)
