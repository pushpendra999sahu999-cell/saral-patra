"""Saral Patra - AI helper that explains confusing official letters in simple Hindi/English.
AWS services: Textract (OCR) + Bedrock (explain) + Polly (voice)."""
import json, os, re
import boto3, streamlit as st

REGION = os.getenv("AWS_REGION", "us-east-1")
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")

textract = boto3.client("textract", region_name=REGION)
bedrock = boto3.client("bedrock-runtime", region_name=REGION)
polly = boto3.client("polly", region_name=REGION)

PROMPT = """You are 'Saral Patra', a kind helper for people who struggle to read official letters
(government notices, bank letters, bills, legal or insurance notices).
Read the document text below and reply ONLY with valid JSON (no markdown) in {lang}, using simple everyday words:
{{
 "doc_type": "what kind of document this is",
 "summary": "2-3 very simple sentences: what this letter says",
 "action_steps": ["step 1", "step 2", "..."],
 "deadline": "deadline/date or 'Not mentioned'",
 "amount": "money involved or 'Not mentioned'",
 "risk_level": "LOW or MEDIUM or HIGH (chance this is a scam/fake or a serious penalty)",
 "red_flags": ["suspicious things like urgent threats, asking OTP/bank details, strange links; empty list if none"],
 "voice_script": "a warm 4-5 sentence spoken explanation as if talking to a grandparent"
}}
Never invent facts. If unclear, say so.

DOCUMENT TEXT:
\"\"\"{text}\"\"\""""


def ocr(image_bytes: bytes) -> str:
    res = textract.detect_document_text(Document={"Bytes": image_bytes})
    return "\n".join(b["Text"] for b in res["Blocks"] if b["BlockType"] == "LINE")


def explain(text: str, lang: str) -> dict:
    resp = bedrock.converse(
        modelId=MODEL_ID,
        messages=[{"role": "user", "content": [{"text": PROMPT.format(lang=lang, text=text[:6000])}]}],
        inferenceConfig={"maxTokens": 1200, "temperature": 0.2},
    )
    raw = resp["output"]["message"]["content"][0]["text"]
    match = re.search(r"\{.*\}", raw, re.S)
    return json.loads(match.group(0))


def speak(text: str, lang: str) -> bytes:
    resp = polly.synthesize_speech(
        Text=text[:2800], OutputFormat="mp3", VoiceId="Kajal", Engine="neural",
        LanguageCode="hi-IN" if lang == "Hindi" else "en-IN",
    )
    return resp["AudioStream"].read()


# ---------------- UI ----------------
st.set_page_config(page_title="Saral Patra", page_icon="📜", layout="centered")
st.title("📜 Saral Patra (सरल पत्र)")
st.caption("Don't understand a notice or bill? Upload it. Get a simple explanation + voice + scam check.")

lang = st.radio("Language / भाषा", ["Hindi", "English"], horizontal=True)
mode = st.radio("Input", ["📷 Upload photo", "⌨️ Paste text (demo)"], horizontal=True)

text = ""
if mode.startswith("📷"):
    f = st.file_uploader("Upload a photo of the letter", type=["png", "jpg", "jpeg"])
    if f:
        st.image(f, width=300)
        if st.button("Explain this letter", type="primary"):
            with st.spinner("Reading document (Textract)..."):
                try:
                    text = ocr(f.getvalue())
                except Exception as e:
                    st.error(f"Textract error: {e}")
else:
    sample = open("sample_notice.txt", encoding="utf-8").read() if os.path.exists("sample_notice.txt") else ""
    pasted = st.text_area("Paste letter text", value=sample, height=200)
    if st.button("Explain this letter", type="primary"):
        text = pasted

if text.strip():
    with st.expander("Text found in document"):
        st.write(text)
    try:
        with st.spinner("Understanding it (Bedrock)..."):
            r = explain(text, lang)
        risk = r.get("risk_level", "LOW").upper()
        color = {"LOW": "green", "MEDIUM": "orange", "HIGH": "red"}.get(risk, "gray")
        icon = {"LOW": "✅", "MEDIUM": "⚠️", "HIGH": "🚨"}.get(risk, "ℹ️")
        st.markdown(f"### {icon} Safety check: :{color}[{risk} RISK]")
        for flag in r.get("red_flags", []):
            st.warning(flag)

        st.subheader(f"📄 {r.get('doc_type', 'Document')}")
        st.info(r.get("summary", ""))
        c1, c2 = st.columns(2)
        c1.metric("📅 Deadline", r.get("deadline", "-"))
        c2.metric("💰 Amount", r.get("amount", "-"))

        st.subheader("✅ What you should do")
        for i, s in enumerate(r.get("action_steps", []), 1):
            st.markdown(f"**{i}.** {s}")

        with st.spinner("Creating voice (Polly)..."):
            st.subheader("🔊 Listen")
            st.audio(speak(r.get("voice_script", r.get("summary", "")), lang), format="audio/mp3")
    except Exception as e:
        st.error(f"Something went wrong: {e}")

st.divider()
st.caption("Built with Amazon Textract • Amazon Bedrock • Amazon Polly | AI can make mistakes - verify with the official office.")
