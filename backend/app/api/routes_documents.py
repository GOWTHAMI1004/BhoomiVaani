import os
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.document import DocumentAnalysisResponse
from app.services.document_service import document_service
from app.config import SAMPLE_DOCS_DIR, settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["Documents"])

@router.post("/analyze", response_model=DocumentAnalysisResponse)
async def analyze_document(file: UploadFile = File(...)):
    """
    Safely extracts and analyzes legal text from uploaded PDF or text file.
    Flags mortgages, unreleased liens, inheritance litigation, and survey discrepancies.
    """
    filename = file.filename or "uploaded_document.txt"
    filename_lower = filename.lower()

    if not (filename_lower.endswith(".pdf") or filename_lower.endswith(".txt")):
        raise HTTPException(
            status_code=400,
            detail="Unsupported format. Only PDF (.pdf) and plain text (.txt) property documents are supported."
        )

    try:
        content_bytes = await file.read()
        max_bytes = settings.max_upload_size_mb * 1024 * 1024

        if len(content_bytes) > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds maximum allowed size of {settings.max_upload_size_mb} MB."
            )

        if len(content_bytes) == 0:
            raise HTTPException(status_code=400, detail="The uploaded file is empty.")

        extracted_text = document_service.extract_text(content_bytes, filename)
        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract readable text from document.")

        analysis = document_service.analyze_document(extracted_text, filename)
        return analysis

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error processing document {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Document analysis failed: {str(e)}")

@router.get("/samples")
def get_sample_documents() -> List[Dict[str, Any]]:
    """
    Returns list of built-in synthetic sample documents for demonstration.
    """
    samples = []
    if os.path.exists(SAMPLE_DOCS_DIR):
        for fname in os.listdir(SAMPLE_DOCS_DIR):
            fpath = SAMPLE_DOCS_DIR / fname
            if fpath.is_file():
                is_disputed = "disputed" in fname.lower()
                samples.append({
                    "id": fname,
                    "filename": fname,
                    "title": fname.replace("_", " ").replace(".txt", "").replace(".pdf", "").title(),
                    "type": "Disputed / Warning Sample" if is_disputed else "Synthetic Document Sample",
                    "size_bytes": fpath.stat().st_size
                })
    return samples

@router.get("/samples/{sample_id}")
def get_sample_document_content(sample_id: str):
    """
    Fetches the content of a synthetic sample document.
    """
    sample_root = SAMPLE_DOCS_DIR.resolve()
    fpath = (sample_root / sample_id).resolve()
    if fpath.parent != sample_root or not fpath.is_file():
        raise HTTPException(status_code=404, detail="Sample document not found.")

    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()

    analysis = document_service.analyze_document(text, sample_id)
    return {
        "filename": sample_id,
        "content": text,
        "analysis": analysis
    }
