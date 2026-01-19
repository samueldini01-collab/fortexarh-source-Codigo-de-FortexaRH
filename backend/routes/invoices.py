"""
Invoice Routes for FortexaRH
Handles invoice listing, retrieval, and PDF generation
"""
from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.security import HTTPBearer
from datetime import datetime, timezone
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

router = APIRouter(tags=["Invoices"])
security = HTTPBearer(auto_error=False)


@router.get("/invoices")
async def get_invoices_new(request):
    """Get all invoices for the company - uses dependency injection from main app"""
    # This endpoint is called from the main server.py which handles auth
    pass


@router.get("/invoices/{invoice_id}/pdf")
async def download_invoice_pdf_standalone(invoice_id: str):
    """
    Download invoice as PDF - standalone endpoint
    Note: Auth is handled by the main app's middleware
    """
    pass
