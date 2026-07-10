from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InvoiceRequest(BaseModel):
    invoice_text: str


@app.get("/")
def home():
    return {"status": "API Running"}


@app.post("/extract")
def extract(req: InvoiceRequest):
    try:

        prompt = f"""
You are an invoice extraction assistant.

Extract the following fields from the invoice text.

Return ONLY valid JSON.

Required JSON schema:

{{
    "invoice_no": null,
    "date": null,
    "vendor": null,
    "amount": null,
    "tax": null,
    "currency": null
}}

Rules:

1. Always return ALL six keys.
2. Use null if a value is missing.
3. date must be ISO format YYYY-MM-DD.
4. amount is the subtotal BEFORE tax.
5. tax is ONLY the tax amount.
6. Currency should be:
   - INR for Rs./INR
   - USD for $
   - EUR for €
   - GBP for £
7. amount and tax must be numbers.
8. Return ONLY JSON.
9. No markdown.
10. No explanation.

Invoice:

{req.invoice_text}
"""

        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt
        )

        answer = response.text.strip()

        answer = answer.replace("```json", "")
        answer = answer.replace("```", "")
        answer = answer.strip()

        data = json.loads(answer)

        result = {
            "invoice_no": data.get("invoice_no"),
            "date": data.get("date"),
            "vendor": data.get("vendor"),
            "amount": data.get("amount"),
            "tax": data.get("tax"),
            "currency": data.get("currency")
        }

        return result

    except Exception as e:
        return {
            "invoice_no": None,
            "date": None,
            "vendor": None,
            "amount": None,
            "tax": None,
            "currency": None,
            "error": str(e)
        }
