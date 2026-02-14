"""
Generated Documents Routes - FortexaRH
Handles saving generated documents and signatures.
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/documents", tags=["Generated Documents"])
security = HTTPBearer(auto_error=False)

db = None
_get_current_user_func = None


def init_router(database, auth_func):
    global db, _get_current_user_func
    db = database
    _get_current_user_func = auth_func


async def get_current_user(request: Request, credentials=Depends(security)):
    if _get_current_user_func is None:
        raise HTTPException(status_code=500, detail="Auth not initialized")
    return await _get_current_user_func(request, credentials)


class GeneratedDocumentCreate(BaseModel):
    template_id: str
    employee_id: str
    content: str
    signature_data: Optional[str] = None


@router.get("")
async def get_documents(current_user: dict = Depends(get_current_user)):
    docs = await db.generated_documents.find(
        {"company_id": current_user.get("company_id")},
        {"_id": 0}
    ).to_list(1000)
    return docs


@router.post("")
async def save_document(data: GeneratedDocumentCreate, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")

    template = await db.templates.find_one({"template_id": data.template_id}, {"_id": 0})
    employee = await db.employees.find_one({"employee_id": data.employee_id, "company_id": company_id}, {"_id": 0})

    doc_id = f"doc_{uuid.uuid4().hex[:12]}"
    document = {
        "document_id": doc_id,
        "company_id": company_id,
        "template_id": data.template_id,
        "template_name": template["name"] if template else "Documento",
        "employee_id": data.employee_id,
        "employee_name": f"{employee['first_name']} {employee['last_name']}" if employee else "Sin asignar",
        "content": data.content,
        "signature_data": data.signature_data,
        "is_signed": bool(data.signature_data),
        "signed_at": datetime.now(timezone.utc).isoformat() if data.signature_data else None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.generated_documents.insert_one(document)
    return {"document_id": doc_id, "message": "Documento guardado correctamente"}


@router.put("/{document_id}/sign")
async def sign_document(document_id: str, signature_data: str, current_user: dict = Depends(get_current_user)):
    result = await db.generated_documents.update_one(
        {"document_id": document_id, "company_id": current_user.get("company_id")},
        {"$set": {
            "signature_data": signature_data,
            "is_signed": True,
            "signed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return {"message": "Documento firmado correctamente"}


@router.get("/{document_id}")
async def get_document(document_id: str, current_user: dict = Depends(get_current_user)):
    doc = await db.generated_documents.find_one(
        {"document_id": document_id, "company_id": current_user.get("company_id")},
        {"_id": 0}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return doc
