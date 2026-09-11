"""
QueueEase AI — Virtual Queue & Guidance Assistant
Hackathon prototype (Streamlit)

Flow:
 1. Conversational Intake      -> user types request; UI language is explicit
                                   (English / Urdu / Roman Urdu switch)
 2. AI Request Classification  -> LLM (Gemini or Claude, whichever key is set)
                                   picks the best-matching service from a
                                   grounded knowledge base; falls back to
                                   keyword matching if no key is configured
 3. AI Document Checklist      -> grounded on services_data.py (never invented)
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
# Generative AI core — supports EITHER Google Gemini (free API key, no card
# needed, get one at https://aistudio.google.com/apikey) OR Anthropic Claude.
# Whichever key is present is used. If neither is set, the app still works
# fully using a rule-based fallback engine, so a demo never breaks.
# ---------------------------------------------------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

AI_PROVIDER = None
gemini_model = None
anthropic_client = None

if GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel("gemini-2.0-flash")
        AI_PROVIDER = "gemini"
    except Exception:
        AI_PROVIDER = None

if AI_PROVIDER is None and ANTHROPIC_API_KEY:
    try:
        import anthropic
        anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        AI_PROVIDER = "anthropic"
    except Exception:
        AI_PROVIDER = None

USE_AI = AI_PROVIDER is not None


def call_llm(prompt: str) -> str:
    """Single entry point that talks to whichever provider is configured."""
    if AI_PROVIDER == "gemini":
        resp = gemini_model.generate_content(prompt)
        return (resp.text or "").strip()
    if AI_PROVIDER == "anthropic":
        resp = anthropic_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in resp.content if hasattr(b, "text")).strip()
    raise RuntimeError("No AI provider configured")


# ---------------------------------------------------------------------------
# UI language strings
# ---------------------------------------------------------------------------
LANG_LABELS = {"en": "English", "ur": "اردو", "roman": "Roman Urdu"}

STRINGS = {
    "en": {
        "caption": "Skip the physical queue — an AI-powered virtual queue & guidance assistant",
        "demo_mode": "Demo mode: no AI key configured, using the reliable rule-based engine. "
                      "Add GEMINI_API_KEY or ANTHROPIC_API_KEY in Secrets for full AI responses.",
        "tab_new": "📝 New Request",
        "tab_status": "🔔 My Token / Status",
        "subheader": "What do you need?",
        "instruction": "Type in your own words — English, Urdu, or Roman Urdu all work.",
        "textarea_label": "Describe your request:",
        "placeholder": "e.g. I need to renew my father's CNIC...",
        "submit": "🔍 Submit & Get Guidance",
        "empty_warning": "Please type your request first.",
        "classifying": "AI is understanding your request...",
        "no_match": "Sorry, we couldn't classify your request. Please add a bit more detail "
                    "(e.g. 'CNIC renewal', 'domicile', 'cardiology doctor').",
        "classified_as": "Classified as",
        "institution": "Institution",
        "department": "Department",
        "checklist": "📋 Document Checklist",
        "token_header": "🎟️ Virtual Token",
        "token_no": "Token No.",
        "people_ahead": "People Ahead",
        "est_wait": "Est. Wait",
        "est_turn": "Estimated turn",
        "check_status": "Check the '{tab}' tab to track your status.",
        "my_tokens": "Your Tokens",
        "no_tokens": "No token issued yet. Start from the 'New Request' tab.",
        "turn_soon": "🔔 Your turn may come in {mins} minute(s) — please arrive now!",
        "remaining": "⏳ Estimated remaining wait: **{mins} min**",
        "footer": "QueueEase AI — Hackathon Prototype · Built with Streamlit + Generative AI · "
                  "Free demo. Not affiliated with NADRA or any government body.",
    },
    "ur": {
        "caption": "لائن میں کھڑے ہونے کی ضرورت نہیں — AI سے چلنے والا ورچوئل قطار اور رہنمائی اسسٹنٹ",
        "demo_mode": "ڈیمو موڈ: کوئی AI کی سیٹ نہیں ہے، اس لیے قابلِ اعتماد rule-based انجن استعمال ہو رہا ہے۔ "
                      "مکمل AI جوابات کے لیے Secrets میں GEMINI_API_KEY یا ANTHROPIC_API_KEY شامل کریں۔",
        "tab_new": "📝 نئی درخواست",
        "tab_status": "🔔 میرا ٹوکن / صورتحال",
        "subheader": "آپ کو کیا چاہیے؟",
        "instruction": "اپنے الفاظ میں لکھیں — انگریزی، اردو، یا رومن اردو، سب چلے گا۔",
        "textarea_label": "اپنی درخواست لکھیں:",
        "placeholder": "مثلاً: مجھے اپنا ڈومیسائل بنوانا ہے...",
        "submit": "🔍 جمع کروائیں اور رہنمائی حاصل کریں",
        "empty_warning": "پہلے اپنی درخواست لکھیں۔",
        "classifying": "AI آپ کی درخواست سمجھ رہا ہے...",
        "no_match": "معذرت، ہم آپ کی درخواست کی درجہ بندی نہیں کر سکے۔ براہِ کرم مزید تفصیل کے ساتھ "
                    "دوبارہ لکھیں (مثلاً 'CNIC تجدید'، 'ڈومیسائل'، 'دل کا ڈاکٹر')۔",
        "classified_as": "درجہ بندی",
        "institution": "ادارہ",
        "department": "شعبہ",
        "checklist": "📋 دستاویزات کی فہرست",
        "token_header": "🎟️ ورچوئل ٹوکن",
        "token_no": "ٹوکن نمبر",
        "people_ahead": "آگے موجود افراد",
        "est_wait": "متوقع انتظار",
        "est_turn": "متوقع باری",
        "check_status": "اپنی صورتحال دیکھنے کے لیے '{tab}' ٹیب چیک کریں۔",
        "my_tokens": "آپ کے ٹوکنز",
        "no_tokens": "ابھی تک کوئی ٹوکن جاری نہیں ہوا۔ 'نئی درخواست' ٹیب سے شروع کریں۔",
        "turn_soon": "🔔 آپ کی باری {mins} منٹ میں آ سکتی ہے — براہِ کرم پہنچ جائیں!",
        "remaining": "⏳ متوقع باقی انتظار: **{mins} منٹ**",
        "footer": "QueueEase AI — ہیکاتھون پروٹوٹائپ · Streamlit + Generative AI سے بنایا گیا · "
                  "مفت ڈیمو۔ نادرا یا کسی بھی سرکاری ادارے سے وابستہ نہیں۔",
    },
    "roman": {
        "caption": "Line mein khare hone ki zaroorat nahi — AI-powered virtual queue & guidance assistant",
        "demo_mode": "Demo mode: koi AI key configure nahi hai, isliye reliable rule-based engine "
                      "use ho raha hai. Full AI responses ke liye Secrets mein GEMINI_API_KEY ya "
                      "ANTHROPIC_API_KEY add karein.",
        "tab_new": "📝 Nayi Request",
        "tab_status": "🔔 Mera Token / Status",
        "subheader": "Aapko kya chahiye?",
        "instruction": "Apni zaban mein likhein — English, Urdu ya Roman Urdu, sab chalega.",
        "textarea_label": "Apni request likhein:",
        "placeholder": "e.g. mujhe apna domicile banwana hai...",
        "submit": "🔍 Submit & Get Guidance",
        "empty_warning": "Pehle apni request likhein.",
        "classifying": "AI aapki request samajh rahi hai...",
        "no_match": "Maazrat, hum aapki request classify nahi kar sakay. Zara mazeed tafseel ke "
                    "sath dobara likhein (e.g. 'CNIC renewal', 'domicile', 'cardiology doctor').",
        "classified_as": "Classified as",
        "institution": "Institution",
        "department": "Department",
        "checklist": "📋 Document Checklist",
        "token_header": "🎟️ Virtual Token",
        "token_no": "Token No.",
        "people_ahead": "People Ahead",
        "est_wait": "Est. Wait",
        "est_turn": "Estimated turn",
        "check_status": "'{tab}' tab mein check karte rahein.",
        "my_tokens": "Aapke Tokens",
        "no_tokens": "Abhi tak koi token issue nahi hua. 'Nayi Request' tab se shuru karein.",
        "turn_soon": "🔔 Aapki baari {mins} minute mein aa sakti hai — please pohnch jayein!",
        "remaining": "⏳ Estimated remaining wait: **{mins} min**",
        "footer": "QueueEase AI — Hackathon Prototype · Built with Streamlit + Generative AI · "
                  "Free & open-source demo. Not affiliated with NADRA or any government body.",
    },
}


# ---------------------------------------------------------------------------
# AI-based classification (much more accurate than plain keyword matching —
# understands intent even with typos, mixed language, or indirect phrasing)
# ---------------------------------------------------------------------------
def ai_classify(user_text: str):
    """Ask the LLM to pick the single best-matching service id from the
    grounded list. Returns the matched service dict, or None."""
    catalog = [
        {"id": s["id"], "institution": s["institution"],
         "department": s["department"], "service": s["service"]}
        for s in SERVICES
    ]
    prompt = f"""You classify citizen requests for a Pakistani public-service queue app.

Allowed services (JSON):
{json.dumps(catalog, ensure_ascii=False)}

Citizen's request (may be English, Urdu, or Roman Urdu, may contain typos):
"{user_text}"

Pick the single best-matching service id from the allowed list above.
If NONE of them genuinely match, return "none".
Respond with ONLY a JSON object, no other text, no markdown fences:
{{"service_id": "<id-or-none>"}}"""

    try:
        raw = call_llm(prompt)
        raw = raw.strip().strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()
        data = json.loads(raw)
        sid = data.get("service_id", "none")
        for s in SERVICES:
            if s["id"] == sid:
                return s
        return None
    except Exception:
        return None


def classify_request(user_text: str):
    if USE_AI:
        result = ai_classify(user_text)
        if result:
            return result
        # AI ran but found nothing confident — try keyword match as a safety net
        return keyword_match(user_text)
    return keyword_match(user_text)


def ai_friendly_summary(user_text: str, matched_service: dict, lang: str) -> str:
    lang_name = {"en": "English", "ur": "Urdu (Urdu script)",
                 "roman": "Roman Urdu (Urdu written in Latin/English letters, "
                          "the way people actually text in Pakistan)"}[lang]
    fallback_map = {
        "en": f"For your request, we've identified '{matched_service['service']}' at "
              f"{matched_service['institution']} — {matched_service['department']}. "
              f"Please bring the documents listed below.",
        "ur": f"آپ کی درخواست کے لیے ہم نے '{matched_service['service']}' "
              f"({matched_service['institution']} — {matched_service['department']}) شناخت کیا ہے۔ "
              f"براہِ کرم نیچے دی گئی فہرست کے مطابق دستاویزات ساتھ لے جائیں۔",
        "roman": f"Aapki request ke liye humne '{matched_service['service']}' "
                 f"({matched_service['institution']} — {matched_service['department']}) "
                 f"identify kiya hai. Neeche di gayi checklist ke mutabiq documents sath le jayein.",
    }
    if not USE_AI:
        return fallback_map[lang]

    prompt = f"""You are QueueEase AI, a warm and clear virtual assistant for Pakistani
government/hospital service visitors. A citizen wrote this request:

"{user_text}"

It has been classified as:
Institution: {matched_service['institution']}
Department: {matched_service['department']}
Service: {matched_service['service']}
Required documents: {', '.join(matched_service['documents'])}

Write a short (3-4 sentences), warm, reassuring confirmation message written
ENTIRELY in {lang_name}, confirming what they need and telling them to check
the checklist below. Do not invent any documents beyond what is listed above.
Return plain text only, no markdown."""

    try:
        text = call_llm(prompt)
        return text.strip() or fallback_map[lang]
    except Exception:
        return fallback_map[lang]


# ---------------------------------------------------------------------------
# Simulated live queue database (would be a Google Sheet / real DB in prod)
# ---------------------------------------------------------------------------
def init_queue_state():
    if "queue" not in st.session_state:
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

if "lang" not in st.session_state:
    st.session_state.lang = "en"

top_left, top_right = st.columns([3, 1])
with top_left:
    st.title("🎫 QueueEase AI")
with top_right:
    st.session_state.lang = st.selectbox(
        "🌐", options=list(LANG_LABELS.keys()),
        format_func=lambda k: LANG_LABELS[k],
        index=list(LANG_LABELS.keys()).index(st.session_state.lang),
        label_visibility="collapsed",
    )

L = STRINGS[st.session_state.lang]
rtl = st.session_state.lang == "ur"
if rtl:
    st.markdown('<style>.stApp{direction:rtl;text-align:right;}</style>', unsafe_allow_html=True)

st.caption(L["caption"])

if not USE_AI:
    st.info(L["demo_mode"], icon="🤖")

tab1, tab2 = st.tabs([L["tab_new"], L["tab_status"]])

# ---------------- TAB 1: New request ----------------
with tab1:
    st.subheader(L["subheader"])
    st.write(L["instruction"])

    user_text = st.text_area(
        L["textarea_label"],
        placeholder=L["placeholder"],
        height=90,
    )

    if st.button(L["submit"], type="primary", use_container_width=True):
        if not user_text.strip():
            st.warning(L["empty_warning"])
        else:
            with st.spinner(L["classifying"]):
                matched = classify_request(user_text)
                time.sleep(0.3)

            if not matched:
                st.error(L["no_match"])
            else:
                summary = ai_friendly_summary(user_text, matched, st.session_state.lang)

                st.success(f"✅ {L['classified_as']}: **{matched['service']}**")
                st.markdown(f"**{L['institution']}:** {matched['institution']}  \n"
                            f"**{L['department']}:** {matched['department']}")
                st.write(summary)

                st.markdown(f"#### {L['checklist']}")
                for doc in matched["documents"]:
                    st.checkbox(doc, key=f"doc_{matched['id']}_{doc}")
                st.caption(f"💰 {matched['fee_note']}")

                st.markdown(f"#### {L['token_header']}")
                entry = issue_token(matched)
                c1, c2, c3 = st.columns(3)
                c1.metric(L["token_no"], entry["token"])
                c2.metric(L["people_ahead"], entry["people_ahead"])
                c3.metric(L["est_wait"], f"{entry['estimated_wait_min']} min")
                st.info(
                    f"📅 {L['est_turn']}: **{entry['estimated_time'].strftime('%I:%M %p')}**. "
                    + L["check_status"].format(tab=L["tab_status"]),
                    icon="⏰",
                )

# ---------------- TAB 2: Status ----------------
with tab2:
    st.subheader(L["my_tokens"])
    if not st.session_state.my_tokens:
        st.write(L["no_tokens"])
    else:
        for t in reversed(st.session_state.my_tokens):
            elapsed = (datetime.now() - t["issued_at"]).total_seconds() / 60
            remaining = max(0, round(t["estimated_wait_min"] - elapsed))
            with st.container(border=True):
                st.markdown(f"**{t['token']}** — {t['service']['service']} "
                            f"({t['service']['institution']})")
                if remaining <= 2:
                    st.warning(L["turn_soon"].format(mins=max(remaining, 0)), icon="🔔")
                else:
                    st.write(L["remaining"].format(mins=remaining))

st.divider()
st.caption(L["footer"])
