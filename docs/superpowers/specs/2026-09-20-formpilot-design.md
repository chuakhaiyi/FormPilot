# FormPilot Design

## Goal

FormPilot is a local-first document extraction and validation tool for Malaysian students. It turns university, scholarship, and internship forms into searchable text, structured fields, validation findings, and a clean JSON export without sending documents to a remote service.

## Scope

The first release has three increments:

1. Upload a PDF or image, run local Tesseract OCR, and display extracted text.
2. Classify the document as university, scholarship, internship, or unknown; extract common fields; and show confidence scores.
3. Apply validation rules, retain lightweight processing metadata in SQLite, export JSON, expose offline status, and include a reproducible evaluation script and small labelled dataset format.

The first release does not include authentication, cloud storage, a chatbot, PaddleOCR, custom deep-learning training, or multi-user workflows.

## Architecture

The backend is a FastAPI application with small service modules:

- `ocr`: converts PDF pages or images to text with Tesseract.
- `classification`: TF-IDF plus scikit-learn logistic regression, with a deterministic keyword fallback when no trained model is available.
- `extraction`: regex and nearby-label heuristics for name, dates, CGPA, programme, institution, email, phone, and identification number.
- `validation`: field presence, CGPA range, date ordering, email and phone format checks.
- `storage`: SQLite metadata and result persistence; uploaded files are processed in memory and are not retained by default.
- `evaluation`: computes field precision/recall/F1, document classification accuracy, processing time, and records failure cases.

The UI is Streamlit and calls the same Python service functions directly for a simple offline deployment. FastAPI remains the stable API boundary for future clients and automated testing.

Docker packages Python, Tesseract, and the application. A single local command starts the UI and API; no network service is required at runtime.

## Data flow

1. User selects a PDF/image.
2. The app validates file type and size.
3. OCR returns text and page-level timing metadata.
4. Classification predicts a document type and confidence.
5. Extraction produces field values, source snippets, and per-field confidence.
6. Validation produces severity, message, and field references.
7. The UI renders the result and offers JSON download.
8. SQLite stores document hash, type, processing time, and result summary only; raw document content is not stored.

## Error handling and privacy

Invalid file types, missing Tesseract, unreadable PDFs, OCR failures, and malformed extracted values return user-readable errors through the API and UI. The application must never claim a field is valid solely because OCR produced text; uncertain or absent fields are visibly flagged. The UI displays an offline/local-processing notice. File size limits and extension/MIME checks are applied at the upload boundary.

## Testing and measurement

The project includes:

- focused unit tests for extraction and validation;
- an API smoke test for upload-to-result flow;
- an evaluation command that reads labelled examples and reports field precision, recall, F1, classification accuracy, and average processing time;
- sample fixtures that cover a clean scan, missing fields, poor OCR, and unusual layout.

Metrics are reported only from the provided evaluation data; no resume claims are hard-coded into the product.

## Acceptance criteria

- A local user can upload a PDF/image and see OCR text.
- A supported sample form receives a document type and structured fields.
- Missing or inconsistent values appear as actionable validation findings.
- A JSON result can be downloaded.
- The app runs without cloud credentials or network calls after dependencies are installed.
- Docker configuration documents the local startup path.
- Tests and evaluation run against sample data and produce measurable output.
