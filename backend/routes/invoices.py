"""
Invoice Routes for FortexaRH
Handles invoice listing, retrieval, and PDF generation
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.security import HTTPBearer
from datetime import datetime, timezone
import logging

router = APIRouter(tags=["Invoices"])
security = HTTPBearer(auto_error=False)

db = None
_get_current_user_func = None

logger = logging.getLogger(__name__)


def init_router(database, auth_dependency):
    """Initialize the router with database and auth dependency"""
    global db, _get_current_user_func
    db = database
    _get_current_user_func = auth_dependency


async def get_current_user(request: Request, credentials=Depends(security)):
    """Wrapper for the injected auth function"""
    if _get_current_user_func is None:
        raise HTTPException(status_code=500, detail="Auth not initialized")
    return await _get_current_user_func(request, credentials)


@router.get("/invoices")
async def get_invoices(current_user: dict = Depends(get_current_user)):
    """Get all invoices for the company"""
    company_id = current_user.get("company_id")
    
    invoices = await db.invoices.find(
        {"company_id": company_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return invoices


@router.get("/invoices/{invoice_id}")
async def get_invoice(invoice_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific invoice"""
    company_id = current_user.get("company_id")
    
    invoice = await db.invoices.find_one(
        {"invoice_id": invoice_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    # Get company info for invoice
    company = await db.companies.find_one(
        {"company_id": company_id},
        {"_id": 0, "name": 1}
    )
    
    invoice["company_name"] = company.get("name", "") if company else ""
    
    return invoice


@router.get("/invoices/{invoice_id}/pdf")
async def download_invoice_pdf(invoice_id: str, current_user: dict = Depends(get_current_user)):
    """Download invoice as PDF"""
    company_id = current_user.get("company_id")
    
    # Get invoice
    invoice = await db.invoices.find_one(
        {"invoice_id": invoice_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    # Get company info
    company = await db.companies.find_one(
        {"company_id": company_id},
        {"_id": 0}
    )
    
    try:
        from services.pdf_service import generate_invoice_pdf
        pdf_bytes = generate_invoice_pdf(invoice, company)
        
        invoice_number = invoice.get('invoice_number', invoice_id)
        filename = f"Factura_{invoice_number}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(pdf_bytes))
            }
        )
    except ImportError as e:
        logger.error(f"PDF service import error: {e}")
        raise HTTPException(status_code=500, detail="Servicio de PDF no disponible")
    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        raise HTTPException(status_code=500, detail="Error al generar el PDF")
