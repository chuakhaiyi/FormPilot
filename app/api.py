from fastapi import FastAPI, File, HTTPException, UploadFile

from .core import process_document, recent_documents, save_metadata

app = FastAPI(title="FormPilot", version="0.1.0")


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True, "offline": True}


@app.get("/documents")
def documents() -> list[dict]:
    return recent_documents()


@app.post("/extract")
async def extract(file: UploadFile = File(...)) -> dict:
    try:
        result = process_document(await file.read(), file.filename or "upload", file.content_type)
        save_metadata(result)
        return result
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=422, detail=f"Could not process document: {error}") from error
