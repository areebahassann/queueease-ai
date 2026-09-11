# services_data.py
# Knowledge base used for (a) rule-based classification fallback and
# (b) grounding the Generative AI prompt so it never hallucinates document
# requirements. Each service has keywords (English + Roman Urdu + Urdu) so
# the app works even without an API key.

SERVICES = [
    {
        "id": "nadra_cnic_new",
        "institution": "NADRA",
        "department": "CNIC Registration Counter",
        "service": "New CNIC (Fresh Application)",
        "keywords": ["new cnic", "nya shanakhti card", "shanakhti card banwana",
                     "first cnic", "پہلا شناختی کارڈ", "نیا شناختی کارڈ"],
        "documents": [
            "Original B-Form / Family Registration Certificate",
            "Two passport-size photographs (white background)",
            "Parents' original CNIC",
            "Proof of residence (utility bill / rent agreement)"
        ],
        "avg_service_time_min": 12,
        "fee_note": "Normal processing fee applies (approx. PKR 750, varies by NADRA notification)."
    },
    {
        "id": "nadra_cnic_renew",
        "institution": "NADRA",
        "department": "CNIC Renewal / Modification Counter",
        "service": "CNIC Renewal / Modification",
        "keywords": ["renew cnic", "cnic renewal", "shanakhti card renew",
                     "cnic banwana hai", "father cnic renew", "abbu ka cnic",
                     "شناختی کارڈ کی تجدید", "cnic update"],
        "documents": [
            "Original expired/expiring CNIC",
            "Two recent passport-size photographs",
            "Proof of residence (if address changed)",
            "Marriage certificate (if marital status changed)"
        ],
        "avg_service_time_min": 10,
        "fee_note": "Renewal fee approx. PKR 750 (normal), higher for urgent/executive processing."
    },
    {
        "id": "nadra_domicile",
        "institution": "Domicile & PRC Office",
        "department": "Domicile Certificate Counter",
        "service": "Domicile Certificate",
        "keywords": ["domicile", "domicile banwana", "permanent resident certificate",
                     "prc banwana", "ڈومیسائل"],
        "documents": [
            "CNIC (applicant + father/husband)",
            "Proof of continuous residence (min. 5 years) in the district",
            "School leaving certificate / matriculation certificate",
            "Two passport-size photographs",
            "Affidavit on judicial stamp paper"
        ],
        "avg_service_time_min": 15,
        "fee_note": "Nominal court-fee stamp required; varies by province/district."
    },
    {
        "id": "passport_new",
        "institution": "Passport Office",
        "department": "Passport Issuance Counter",
        "service": "New / Renewed Passport",
        "keywords": ["passport", "passport banwana", "passport renew", "پاسپورٹ"],
        "documents": [
            "Original CNIC",
            "Previous passport (if renewal)",
            "Passport application form (Form-V) printed after online submission",
            "Fee payment receipt (bank/online)"
        ],
        "avg_service_time_min": 14,
        "fee_note": "Fee depends on booklet type (36/72 pages) and urgency (normal/urgent/executive)."
    },
    {
        "id": "hospital_opd_cardiology",
        "institution": "Hospital",
        "department": "Outpatient Cardiology (OPD)",
        "service": "Cardiology Consultation",
        "keywords": ["cardiologist", "dil ka doctor", "heart doctor", "cardiology",
                     "chest pain doctor", "دل کا ڈاکٹر"],
        "documents": [
            "Hospital MR / patient card (or CNIC to generate one)",
            "Previous prescriptions or medical reports, if any",
            "Referral slip (if referred from another department)"
        ],
        "avg_service_time_min": 8,
        "fee_note": "OPD token fee (varies: free in public hospitals, nominal in others)."
    },
    {
        "id": "hospital_opd_general",
        "institution": "Hospital",
        "department": "General Outpatient (OPD)",
        "service": "General Physician Consultation",
        "keywords": ["general doctor", "opd", "bukhar", "fever doctor", "checkup",
                     "ڈاکٹر کو دکھانا"],
        "documents": [
            "Hospital MR / patient card (or CNIC to generate one)",
            "Previous prescriptions, if any"
        ],
        "avg_service_time_min": 6,
        "fee_note": "OPD token fee (varies by hospital)."
    },
    {
        "id": "utility_bill",
        "institution": "Utility Company (Electricity/Gas/Water)",
        "department": "Bill Payment / Complaint Counter",
        "service": "Bill Correction / New Connection / Complaint",
        "keywords": ["bijli ka bill", "gas ka bill", "utility bill", "new connection",
                     "meter complaint", "بجلی کا بل", "گیس کا بل"],
        "documents": [
            "Copy of most recent bill",
            "CNIC of account holder",
            "Proof of ownership/tenancy (for new connection)"
        ],
        "avg_service_time_min": 9,
        "fee_note": "Connection charges vary by load/type; corrections are usually free."
    },
]

def keyword_match(user_text: str):
    """Rule-based fallback classifier (no API needed). Uses forgiving
    word-overlap scoring instead of rigid substring matching, so phrases
    like 'renew my father's CNIC' still match 'cnic renewal' keywords even
    though the words appear in a different order."""
    text_words = set(user_text.lower().replace("'", "").split())
    best, best_score = None, 0
    for svc in SERVICES:
        score = 0
        for kw in svc["keywords"]:
            kw_lower = kw.lower()
            if kw_lower in user_text.lower():
                score += 3  # exact phrase match — strong signal
            else:
                kw_words = set(kw_lower.replace("'", "").split())
                overlap = len(kw_words & text_words)
                if overlap >= 1 and overlap == len(kw_words):
                    score += 2  # all keyword words present, different order
                elif overlap >= 1:
                    score += overlap * 0.5  # partial word overlap
        if score > best_score:
            best, best_score = svc, score
    return best if best_score >= 1 else None
