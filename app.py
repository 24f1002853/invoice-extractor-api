from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dateutil import parser
import re

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


def search_patterns(patterns, text):
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if m:
            return m.group(1).strip()
    return None


def clean_amount(value):
    if value is None:
        return None

    value = re.sub(r"(Rs\.?|INR|USD|\$|EUR|€|GBP|£)", "", value, flags=re.IGNORECASE)
    value = value.replace(",", "").strip()

    try:
        return float(value)
    except:
        return None


@app.get("/")
def home():
    return {"status": "API Running"}


@app.post("/extract")
def extract(req: InvoiceRequest):

    text = req.invoice_text

    invoice_no = search_patterns([
        r"Invoice\s*No\.?\s*[:#]?\s*([A-Za-z0-9\-\/]+)",
        r"Invoice\s*Number\s*[:#]?\s*([A-Za-z0-9\-\/]+)",
        r"Invoice\s*#\s*([A-Za-z0-9\-\/]+)",
        r"Reference\s*[:#]?\s*([A-Za-z0-9\-\/]+)",
        r"Ref\s*[:#]?\s*([A-Za-z0-9\-\/]+)"
    ], text)

    vendor = search_patterns([
        r"Vendor\s*:\s*(.+)",
        r"Supplier\s*:\s*(.+)",
        r"Client\s*:\s*(.+)",
        r"Seller\s*:\s*(.+)"
    ], text)

    date_text = search_patterns([
        r"Date\s*:\s*(.+)",
        r"Issued\s*:\s*(.+)",
        r"Invoice\s*Date\s*:\s*(.+)"
    ], text)

    subtotal = search_patterns([
        r"Subtotal\s*:\s*(.+)",
        r"Sub\s*Total\s*:\s*(.+)"
    ], text)

    tax = search_patterns([
        r"GST.*?:\s*(.+)",
        r"IGST.*?:\s*(.+)",
        r"CGST.*?:\s*(.+)",
        r"SGST.*?:\s*(.+)",
        r"VAT.*?:\s*(.+)",
        r"Tax.*?:\s*(.+)"
    ], text)

    currency = None

    if re.search(r"Rs\.?|INR", text, re.IGNORECASE):
        currency = "INR"
    elif "$" in text or re.search(r"\bUSD\b", text):
        currency = "USD"
    elif "€" in text or re.search(r"\bEUR\b", text):
        currency = "EUR"
    elif "£" in text or re.search(r"\bGBP\b", text):
        currency = "GBP"

    iso_date = None

    if date_text:
        try:
            iso_date = parser.parse(date_text).date().isoformat()
        except:
            iso_date = None

    return {
        "invoice_no": invoice_no,
        "date": iso_date,
        "vendor": vendor,
        "amount": clean_amount(subtotal),
        "tax": clean_amount(tax),
        "currency": currency
    }
