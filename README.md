---
title: QueueEase AI
emoji: 🎫
colorFrom: green
colorTo: blue
sdk: streamlit
sdk_version: "1.37.0"
app_file: app.py
pinned: false
---

# 🎫 QueueEase AI — Virtual Queue & Guidance Assistant

A Generative-AI-powered virtual queue and guidance assistant for Pakistani
public/semi-public institutions (NADRA, hospitals, domicile/passport offices,
utility counters). Users describe what they need in **English, Urdu, or Roman
Urdu**, and instantly get:

- ✅ Correct institution/department classification
- 📋 AI-generated document checklist
- 🎟️ Virtual token number
- ⏱️ Estimated wait time
- 🔔 Simulated "your turn is coming" notification

Built for a hackathon — lightweight, free-tier friendly, and fully working
out of the box (works even without an API key, using a smart rule-based
fallback engine).

---

## 🚀 Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL Streamlit prints (usually http://localhost:8501).

### (Optional) Enable full Generative AI responses

By default the app runs in **demo mode** using a reliable rule-based engine —
perfect for live demos/recordings since it never fails. To turn on live
Claude-generated responses:

```bash
export ANTHROPIC_API_KEY="your-key-here"
streamlit run app.py
```

---

## ☁️ Deploy for FREE (2 options)

### Option A — Hugging Face Spaces (recommended, easiest)

1. Create a free account at https://huggingface.co
2. Click **New Space** → choose **Streamlit** as the SDK → name it `queueease-ai`
3. Upload these 3 files (or connect the GitHub repo below): `app.py`,
   `services_data.py`, `requirements.txt`
4. (Optional) Go to **Settings → Repository secrets** → add
   `ANTHROPIC_API_KEY` to enable full AI responses
5. The Space auto-builds and gives you a public URL — this is your
   **"Application working Link"**

### Option B — GitHub + Streamlit Community Cloud

1. Push this folder to a new GitHub repo (see commands below)
2. Go to https://share.streamlit.io → **New app** → select your repo/branch
   → main file path `app.py`
3. (Optional) In **Advanced settings → Secrets**, add:
   ```
   ANTHROPIC_API_KEY = "your-key-here"
   ```
4. Deploy — you get a free public `*.streamlit.app` URL

### Push to GitHub

```bash
git init
git add .
git commit -m "QueueEase AI - hackathon submission"
git branch -M main
git remote add origin https://github.com/<your-username>/queueease-ai.git
git push -u origin main
```

---

## 🧠 How it works (architecture)

1. **Conversational Intake** — a text box accepts natural language in any of
   the three languages/scripts.
2. **AI Request Classification** — `services_data.py` holds a grounded
   knowledge base (institution → department → service → keywords). A
   keyword-matching engine classifies instantly; if `ANTHROPIC_API_KEY` is
   set, Claude also writes a warm, bilingual confirmation message grounded
   strictly in that matched record (no hallucinated documents).
3. **Document Checklist** — pulled directly from the grounded knowledge base
   per matched service.
4. **Virtual Token & Wait-Time Prediction** — `st.session_state.queue`
   simulates a live queue (stand-in for the Google Sheet described in the
   original PRD); wait time = people ahead × average service time for that
   counter.
5. **Smart Notification** — the "Mera Token / Status" tab recalculates
   remaining wait live and shows an alert once it drops below 2 minutes.

## 📁 Files

```
queueease-ai/
├── app.py              # Streamlit application (all UI + logic)
├── services_data.py    # Grounded knowledge base + rule-based classifier
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## ⚠️ Disclaimer

Hackathon prototype for demonstration purposes only. Not affiliated with
NADRA, any hospital, or any government body. Document requirements should be
verified with the relevant institution before a real visit.
