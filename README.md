# 📜 Saral Patra (सरल पत्र)
Voice-first AI that explains confusing official letters (notices, bills, bank/legal letters) in simple Hindi, with a scam check.
**Problem:** Millions can't read complex official documents and lose money or fall for scams.
**Flow:** Photo -> Amazon Textract (OCR) -> Amazon Bedrock (explain + scam analysis) -> Amazon Polly (Hindi voice).

## Run
```
pip install -r requirements.txt
aws configure            # access key, secret, region (us-east-1 recommended)
streamlit run app.py
```
Optional: `export BEDROCK_MODEL_ID=amazon.nova-lite-v1:0` (or any enabled model; use `us.amazon.nova-lite-v1:0` if asked for an inference profile).

## Before running
1. AWS Console -> Bedrock -> Model access -> enable Amazon Nova Lite (or Claude).
2. IAM user needs: `textract:DetectDocumentText`, `bedrock:InvokeModel`, `polly:SynthesizeSpeech`.

## Demo tip
Use "Paste text (demo)" with the included scam sample: it shows a HIGH RISK warning + Hindi audio.

## Future scope
WhatsApp bot, Chhattisgarhi/Marathi support, PDF support, one-tap "report scam" to cybercrime.gov.in.
