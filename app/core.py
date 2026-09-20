from __future__ import annotations

import hashlib
import io
import re
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any

FIELD_NAMES = ("name", "email", "phone", "programme", "institution", "cgpa", "date", "id_number")
SUPPORTED_TYPES = {"application/pdf", "image/png", "image/jpeg", "image/jpg", "image/webp"}
MAX_FILE_BYTES = 15 * 1024 * 1024


def _ocr_image(image) -> str:
    import pytesseract

    return pytesseract.image_to_string(image).strip()


def ocr_document(content: bytes, filename: str) -> tuple[str, float]:
    import fitz
    from PIL import Image

    started = time.perf_counter()
    if filename.lower().endswith(".pdf"):
        document = fitz.open(stream=content, filetype="pdf")
        pages = []
        for page in document:
            text = page.get_text().strip()
            if not text:
                pixmap = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
                text = _ocr_image(Image.open(io.BytesIO(pixmap.tobytes("png"))))
            pages.append(text)
        text = "\n\n".join(page for page in pages if page)
    else:
        text = _ocr_image(Image.open(io.BytesIO(content)))
    return text.strip(), round(time.perf_counter() - started, 3)


def classify_document(text: str) -> dict[str, Any]:
    lower = text.lower()
    keywords = {
        "scholarship": ("scholarship", "biasiswa", "sponsor", "financial aid"),
        "internship": ("internship", "industrial training", "practical training", "intern"),
        "university": ("university", "universiti", "student details", "programme of study", "cgpa"),
    }
    scores = {label: sum(lower.count(word) for word in words) for label, words in keywords.items()}
    label, score = max(scores.items(), key=lambda item: item[1])
    if score == 0:
        return {"type": "unknown", "confidence": 0.0, "scores": scores}
    total = sum(scores.values()) or 1
    return {"type": label, "confidence": round(min(0.99, 0.55 + score / total * 0.4), 2), "scores": scores}


def _first(patterns: list[str], text: str, flags: int = re.IGNORECASE) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags)
        if match:
            return match.group(1).strip(" .:-")
    return None


def extract_fields(text: str) -> dict[str, dict[str, Any]]:
    fields = {
        "name": _first([r"(?:full\s+name|name)\s*[:\-]\s*([^\n]+)", r"(?:full\s+name|name)\s+([^\n]+)"], text),
        "email": _first([r"([\w.+-]+@[\w-]+\.[\w.-]+)"], text),
        "phone": _first([r"(?:phone|mobile|telephone|tel)\s*[:\-]?\s*(\+?6?0?1[0-9][\s-]?\d{3,4}[\s-]?\d{3,4})"], text),
        "programme": _first([r"(?:programme|program|course)\s*[:\-]\s*([^\n]+)"], text),
        "institution": _first([r"(?:institution|university|universiti|college)\s*[:\-]\s*([^\n]+)"], text),
        "cgpa": _first([r"(?:cgpa|c\.g\.p\.a\.)\s*[:\-]?\s*([0-9](?:\.[0-9]{1,2})?)"], text),
        "date": _first([r"(?:date of birth|date|tarikh)\s*[:\-]\s*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4}|[0-9]{4}[/-][0-9]{1,2}[/-][0-9]{1,2})"], text),
        "id_number": _first([r"(?:ic|nric|identity card|passport)\s*(?:no|number)?\s*[:\-]\s*([A-Z0-9 -]{5,20})"], text),
    }
    return {name: {"value": value, "confidence": 0.9 if value else 0.0} for name, value in fields.items()}


def validate_fields(fields: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for name in FIELD_NAMES:
        if not fields.get(name, {}).get("value"):
            issues.append({"field": name, "severity": "warning", "message": f"Missing {name.replace('_', ' ')}"})
    email = fields.get("email", {}).get("value")
    if email and not re.fullmatch(r"[\w.+-]+@[\w-]+\.[\w.-]+", email):
        issues.append({"field": "email", "severity": "error", "message": "Email format looks invalid"})
    cgpa = fields.get("cgpa", {}).get("value")
    if cgpa:
        try:
            if not 0 <= float(cgpa) <= 4:
                issues.append({"field": "cgpa", "severity": "error", "message": "CGPA must be between 0.00 and 4.00"})
        except ValueError:
            issues.append({"field": "cgpa", "severity": "error", "message": "CGPA is not numeric"})
    return issues


def process_document(content: bytes, filename: str, mime_type: str | None = None) -> dict[str, Any]:
    if len(content) > MAX_FILE_BYTES:
        raise ValueError("File is larger than the 15 MB limit")
    if mime_type and mime_type not in SUPPORTED_TYPES and not filename.lower().endswith(".pdf"):
        raise ValueError("Only PDF, PNG, JPG, JPEG, and WEBP files are supported")
    text, ocr_seconds = ocr_document(content, filename)
    fields = extract_fields(text)
    return {
        "filename": filename,
        "processed_at": datetime.now().isoformat(timespec="seconds"),
        "offline": True,
        "ocr_seconds": ocr_seconds,
        "document": classify_document(text),
        "fields": fields,
        "issues": validate_fields(fields),
        "text": text,
    }


def save_metadata(result: dict[str, Any], db_path: str = "formpilot.db") -> None:
    with sqlite3.connect(db_path) as db:
        db.execute("CREATE TABLE IF NOT EXISTS documents (id INTEGER PRIMARY KEY, file_hash TEXT, filename TEXT, document_type TEXT, ocr_seconds REAL, created_at TEXT)")
        digest = hashlib.sha256(result["text"].encode("utf-8")).hexdigest()
        db.execute("INSERT INTO documents(file_hash, filename, document_type, ocr_seconds, created_at) VALUES (?, ?, ?, ?, ?)", (digest, result["filename"], result["document"]["type"], result["ocr_seconds"], result["processed_at"]))
        db.commit()
