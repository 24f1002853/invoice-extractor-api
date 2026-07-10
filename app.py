from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dateutil import parser
import re

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class InvoiceRequest(BaseModel):
    invoice_text: str


def extract_value(pattern, text):
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def clean_amount(value):
    if value is None:
        return None

    value = value.replace(",", "")
    value = re.sub(r"Rs\.?|INR", "", value, flags=re.IGNORECASE).strip()

    try:
        return float(value)
    except:
        return None


@app.get("/")
def root():
    return {"status": "API Running"}


@app.post("/extract")
def extract_invoice(req: InvoiceRequest):

    text = req.invoice_text

    invoice_no = extract_value(
        r"Invoice\s*(?:No|Number)?\s*[:#]?\s*([A-Za-z0-9\-\/]+)",
        text,
    )

    vendor = extract_value(
        r"Vendor\s*[:]\s*(.+)",
        text,
    )

    date_str = extract_value(
        r"Date\s*[:]\s*(.+)",
        text,
    )

    subtotal = extract_value(
        r"(?:Subtotal|Sub Total)\s*[:]\s*(.+)",
        text,
    )

    tax = extract_value(
        r"(?:GST|Tax|VAT).*?[:]\s*(.+)",
        text,
    )

    currency = None

    if re.search(r"Rs\.?|INR", text, re.IGNORECASE):
        currency = "INR"

    iso_date = None

    if date_str:
        try:
            iso_date = parser.parse(date_str).date().isoformat()
        except:
            iso_date = None

    return {
        "invoice_no": invoice_no,
        "date": iso_date,
        "vendor": vendor,
        "amount": clean_amount(subtotal),
        "tax": clean_amount(tax),
        "currency": currency,
    }