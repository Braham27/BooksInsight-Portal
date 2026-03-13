import base64
import json
import uuid

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None
import structlog
from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.document import DocStatus, Document
from app.utils.storage import storage_service

logger = structlog.get_logger()

W2_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "doc_type": {
            "type": "string",
            "enum": ["W2", "1099_INT", "1099_DIV", "1099_B", "OTHER"],
            "description": "The type of tax document detected",
        },
        "fields": {
            "type": "object",
            "properties": {
                "employer_name": {"type": "string"},
                "employer_ein": {"type": "string"},
                "employee_name": {"type": "string"},
                "ssn_last4": {
                    "type": "string",
                    "description": "Last 4 digits of SSN only. Do NOT extract the full SSN.",
                },
                "wages_box1": {"type": "number", "description": "Box 1: Wages, tips, other compensation"},
                "fed_withheld_box2": {"type": "number", "description": "Box 2: Federal income tax withheld"},
                "ss_wages_box3": {"type": "number", "description": "Box 3: Social security wages"},
                "ss_tax_box4": {"type": "number", "description": "Box 4: Social security tax withheld"},
                "medicare_wages_box5": {"type": "number", "description": "Box 5: Medicare wages and tips"},
                "medicare_tax_box6": {"type": "number", "description": "Box 6: Medicare tax withheld"},
                "state": {"type": "string", "description": "Box 15: State"},
                "state_wages": {"type": "number", "description": "Box 16: State wages"},
                "state_tax_withheld": {"type": "number", "description": "Box 17: State income tax"},
            },
        },
        "confidence": {
            "type": "object",
            "description": "Confidence score (0.0 to 1.0) for each extracted field",
            "additionalProperties": {"type": "number"},
        },
    },
    "required": ["doc_type", "fields", "confidence"],
}

EXTRACTION_SYSTEM_PROMPT = """You are a tax document extraction agent. Your job is to extract structured data from tax documents (W-2, 1099, etc.).

Rules:
1. Extract ONLY the data visible in the document.
2. Do NOT compute, interpret, or infer any tax implications.
3. For SSN, extract ONLY the last 4 digits. Never include the full SSN.
4. Provide a confidence score (0.0 to 1.0) for each extracted field.
5. If a field is not visible or unreadable, omit it and set confidence to 0.
6. Classify the document type (W2, 1099_INT, 1099_DIV, 1099_B, OTHER).
7. All monetary values should be numbers (not strings).

Return valid JSON matching the schema provided."""


async def _convert_pdf_to_images(file_content: bytes) -> list[bytes]:
    """Convert PDF pages to PNG images for GPT-4 Vision."""
    images = []
    doc = fitz.open(stream=file_content, filetype="pdf")
    for page in doc:
        # Render at 2x resolution for better OCR
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        images.append(pix.tobytes("png"))
    doc.close()
    return images


async def extract_document(
    db: AsyncSession,
    document_id: str,
) -> dict:
    """Extract structured data from a tax document using GPT-4 Vision."""
    doc = await db.get(Document, document_id)
    if not doc:
        raise ValueError(f"Document {document_id} not found")

    # Update status to processing
    doc.status = DocStatus.PROCESSING
    await db.flush()

    try:
        file_content = await storage_service.read_file(doc.file_path)

        # Convert to images if PDF
        if doc.mime_type == "application/pdf":
            images = await _convert_pdf_to_images(file_content)
        else:
            images = [file_content]

        # Build GPT-4 Vision request
        client = AsyncOpenAI(api_key=settings.openai_api_key)

        image_messages = []
        for img in images:
            b64 = base64.b64encode(img).decode("utf-8")
            mime = "image/png" if doc.mime_type == "application/pdf" else doc.mime_type
            image_messages.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{b64}", "detail": "high"},
                }
            )

        response = await client.chat.completions.create(
            model=settings.openai_vision_model,
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Extract all fields from this tax document. "
                                "Return JSON matching the extraction schema. "
                                "Remember: only last 4 digits of SSN."
                            ),
                        },
                        *image_messages,
                    ],
                },
            ],
            response_format={"type": "json_object"},
            max_tokens=2000,
            temperature=0,
        )

        result_text = response.choices[0].message.content
        result = json.loads(result_text)

        # Build evidence map from confidence scores
        evidence = {}
        for field_name, score in result.get("confidence", {}).items():
            evidence[field_name] = {
                "confidence": score,
                "source_document": str(document_id),
                "extractor": "gpt4-vision",
            }

        # Detect warnings
        warnings = []
        for field_name, score in result.get("confidence", {}).items():
            if score < 0.8:
                warnings.append(
                    f"Low confidence ({score:.0%}) on field '{field_name}'"
                )

        # Update document
        doc.extracted_data = result.get("fields", {})
        doc.doc_type = result.get("doc_type", "OTHER")
        doc.evidence = evidence
        doc.status = DocStatus.EXTRACTED
        await db.flush()

        logger.info(
            "document_extracted",
            document_id=str(document_id),
            doc_type=doc.doc_type,
            field_count=len(result.get("fields", {})),
        )

        return {
            "document_id": str(document_id),
            "doc_type": doc.doc_type,
            "extracted_data": doc.extracted_data,
            "evidence": evidence,
            "warnings": warnings,
        }

    except Exception as e:
        doc.status = DocStatus.ERROR
        await db.flush()
        logger.error("extraction_failed", document_id=str(document_id), error=str(e))
        raise
