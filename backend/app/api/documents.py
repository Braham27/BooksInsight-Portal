from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.clerk import AuthUser, get_current_user
from app.database import get_db
from app.models.case import Case
from app.models.document import Document, DocStatus
from app.schemas.document import DocumentResponse, DocumentUpdateRequest
from app.services import audit_service
from app.utils.storage import storage_service

router = APIRouter(prefix="/cases/{case_id}/documents", tags=["documents"])


async def _get_case_with_access(
    case_id: str, user: AuthUser, db: AsyncSession
) -> Case:
    case = await db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.user_id != user.user_id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return case


@router.post("", response_model=DocumentResponse, status_code=201)
async def upload_document(
    case_id: str,
    file: UploadFile,
    request: Request,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    case = await _get_case_with_access(case_id, user, db)

    content = await file.read()

    try:
        file_path = await storage_service.save_file(
            content=content,
            filename=file.filename or "upload",
            mime_type=file.content_type or "application/octet-stream",
            case_id=case_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    doc = Document(
        case_id=case_id,
        file_path=file_path,
        file_name=file.filename or "upload",
        file_size=len(content),
        mime_type=file.content_type or "application/octet-stream",
        status=DocStatus.UPLOADED,
    )
    db.add(doc)
    await db.flush()

    await audit_service.log_event(
        db,
        user_id=user.user_id,
        action="document_uploaded",
        entity_type="document",
        entity_id=doc.id,
        case_id=case_id,
        new_value={"file_name": doc.file_name, "mime_type": doc.mime_type, "size": doc.file_size},
        ip_address=request.client.host if request.client else None,
    )

    return doc


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    case_id: str,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_case_with_access(case_id, user, db)
    result = await db.execute(
        select(Document)
        .where(Document.case_id == case_id)
        .order_by(Document.created_at)
    )
    return result.scalars().all()


@router.patch("/{doc_id}", response_model=DocumentResponse)
async def update_document(
    case_id: str,
    doc_id: str,
    body: DocumentUpdateRequest,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_case_with_access(case_id, user, db)
    doc = await db.get(Document, doc_id)
    if not doc or doc.case_id != case_id:
        raise HTTPException(status_code=404, detail="Document not found")

    old_data = doc.extracted_data

    if body.extracted_data is not None:
        doc.extracted_data = body.extracted_data
        doc.status = DocStatus.VERIFIED
    if body.doc_type is not None:
        doc.doc_type = body.doc_type

    await db.flush()

    await audit_service.log_event(
        db,
        user_id=user.user_id,
        action="document_updated",
        entity_type="document",
        entity_id=doc.id,
        case_id=case_id,
        old_value=old_data,
        new_value=doc.extracted_data,
    )

    return doc
