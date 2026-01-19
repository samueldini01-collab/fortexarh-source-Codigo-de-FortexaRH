"""
Invoice Routes for FortexaRH
Handles invoice listing, retrieval, and PDF generation
"""
from fastapi import APIRouter, HTTPException, Depends, Response
from datetime import datetime, timezone
import logging

router = APIRouter(prefix="/invoices", tags=["Invoices"])

# These will be injected from server.py
db = None
get_current_user = None

def init_router(database, auth_dependency):
    """Initialize router with database and auth dependency"""
    global db, get_current_user
    db = database
    get_current_user = auth_dependency


@router.get("")
async def get_invoices(current_user: dict = Depends(lambda: get_current_user)):
    """Get all invoices for the company"""
    if get_current_user is None:
        raise HTTPException(status_code=500, detail="Router not initialized")
    
    # Re-fetch current user to ensure we have the dependency
    user = current_user
    company_id = user.get("company_id")
    
    invoices = await db.invoices.find(
        {"company_id": company_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return invoices


@router.get("/{invoice_id}")
async def get_invoice(invoice_id: str, current_user: dict = Depends(lambda: get_current_user)):
    """Get a specific invoice"""
    if get_current_user is None:
        raise HTTPException(status_code=500, detail="Router not initialized")
    
    user = current_user
    company_id = user.get("company_id")
    
    invoice = await db.invoices.find_one(
        {"invoice_id": invoice_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    # Get company info
    company = await db.companies.find_one(
        {"company_id": company_id},
        {"_id": 0, "name": 1, "address": 1, "phone": 1}
    )
    
    invoice["company_name"] = company.get("name", "") if company else ""
    
    return invoice


@router.get("/{invoice_id}/pdf")
async def download_invoice_pdf(invoice_id: str, current_user: dict = Depends(lambda: get_current_user)):
    """Download invoice as PDF"""
    if get_current_user is None:
        raise HTTPException(status_code=500, detail="Router not initialized")
    
    user = current_user
    company_id = user.get("company_id")
    
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
        logging.error(f"PDF service import error: {e}")
        raise HTTPException(status_code=500, detail="Servicio de PDF no disponible. Instale reportlab.")
    except Exception as e:
        logging.error(f"PDF generation error: {e}")
        raise HTTPException(status_code=500, detail="Error al generar el PDF")
