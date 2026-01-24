"""
Support Ticket System
Handles customer support requests from the landing page
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timezone
import os
import resend

router = APIRouter(prefix="/support", tags=["Support"])

# Resend configuration
resend.api_key = os.environ.get('RESEND_API_KEY', '')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'noreply@fortexarh.com')
SUPPORT_EMAIL = os.environ.get('INFO_EMAIL', 'soporte@fortexarh.com')

# MongoDB reference (will be set by init_router)
db = None


def init_router(database):
    global db
    db = database


class SupportTicketRequest(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None
    phone: Optional[str] = None
    category: str
    priority: str = "medium"
    subject: str
    message: str


class SupportTicketResponse(BaseModel):
    ticket_id: str
    message: str
    status: str


CATEGORY_LABELS = {
    "general": "Consulta General",
    "technical": "Soporte Técnico",
    "bug": "Reporte de Error",
    "billing": "Facturación y Pagos",
    "account": "Mi Cuenta",
    "demo": "Solicitud de Demo",
    "enterprise": "Plan Enterprise",
}

PRIORITY_LABELS = {
    "low": "Baja",
    "medium": "Media",
    "high": "Alta",
    "critical": "Crítica",
}

PRIORITY_COLORS = {
    "low": "#6b7280",
    "medium": "#3b82f6",
    "high": "#f59e0b",
    "critical": "#ef4444",
}


@router.post("/ticket", response_model=SupportTicketResponse)
async def create_support_ticket(ticket: SupportTicketRequest):
    """
    Create a new support ticket and send notification emails
    """
    try:
        # Generate ticket ID
        ticket_id = f"TKT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        
        # Store ticket in database
        ticket_data = {
            "ticket_id": ticket_id,
            "name": ticket.name,
            "email": ticket.email,
            "company": ticket.company,
            "phone": ticket.phone,
            "category": ticket.category,
            "category_label": CATEGORY_LABELS.get(ticket.category, ticket.category),
            "priority": ticket.priority,
            "priority_label": PRIORITY_LABELS.get(ticket.priority, ticket.priority),
            "subject": ticket.subject,
            "message": ticket.message,
            "status": "open",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "responses": []
        }
        
        if db is not None:
            await db.support_tickets.insert_one(ticket_data)
        
        # Send email to support team
        try:
            support_email_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #10b981, #14b8a6); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                    .content {{ background: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; }}
                    .field {{ margin-bottom: 15px; }}
                    .label {{ font-weight: bold; color: #6b7280; font-size: 12px; text-transform: uppercase; }}
                    .value {{ margin-top: 4px; }}
                    .priority {{ display: inline-block; padding: 4px 12px; border-radius: 20px; color: white; font-size: 12px; font-weight: bold; }}
                    .message-box {{ background: white; padding: 15px; border-radius: 8px; border: 1px solid #e5e7eb; margin-top: 15px; }}
                    .footer {{ text-align: center; padding: 15px; color: #6b7280; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2 style="margin: 0;">🎫 Nuevo Ticket de Soporte</h2>
                        <p style="margin: 5px 0 0 0; opacity: 0.9;">#{ticket_id}</p>
                    </div>
                    <div class="content">
                        <div class="field">
                            <div class="label">Prioridad</div>
                            <div class="value">
                                <span class="priority" style="background: {PRIORITY_COLORS.get(ticket.priority, '#6b7280')}">
                                    {PRIORITY_LABELS.get(ticket.priority, ticket.priority)}
                                </span>
                            </div>
                        </div>
                        <div class="field">
                            <div class="label">Categoría</div>
                            <div class="value">{CATEGORY_LABELS.get(ticket.category, ticket.category)}</div>
                        </div>
                        <div class="field">
                            <div class="label">De</div>
                            <div class="value">
                                <strong>{ticket.name}</strong><br>
                                {ticket.email}<br>
                                {f"Empresa: {ticket.company}" if ticket.company else ""}
                                {f"<br>Tel: {ticket.phone}" if ticket.phone else ""}
                            </div>
                        </div>
                        <div class="field">
                            <div class="label">Asunto</div>
                            <div class="value"><strong>{ticket.subject}</strong></div>
                        </div>
                        <div class="message-box">
                            <div class="label">Mensaje</div>
                            <div class="value" style="white-space: pre-wrap;">{ticket.message}</div>
                        </div>
                    </div>
                    <div class="footer">
                        FortexaRH - Sistema de RRHH y Nómina<br>
                        Este ticket fue creado desde el formulario de soporte.
                    </div>
                </div>
            </body>
            </html>
            """
            
            resend.Emails.send({
                "from": f"FortexaRH Soporte <{SENDER_EMAIL}>",
                "to": [SUPPORT_EMAIL],
                "subject": f"[{ticket.priority.upper()}] {ticket.subject} - {ticket_id}",
                "html": support_email_html,
                "reply_to": ticket.email
            })
        except Exception as e:
            print(f"Error sending support team email: {e}")
        
        # Send confirmation email to customer
        try:
            customer_email_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #10b981, #14b8a6); color: white; padding: 30px; border-radius: 8px 8px 0 0; text-align: center; }}
                    .content {{ background: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; }}
                    .ticket-box {{ background: white; padding: 20px; border-radius: 8px; border: 1px solid #e5e7eb; text-align: center; margin: 20px 0; }}
                    .ticket-id {{ font-size: 24px; font-weight: bold; color: #10b981; font-family: monospace; }}
                    .info {{ background: #ecfdf5; padding: 15px; border-radius: 8px; border-left: 4px solid #10b981; }}
                    .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1 style="margin: 0;">✅ Solicitud Recibida</h1>
                        <p style="margin: 10px 0 0 0; opacity: 0.9;">Gracias por contactar a FortexaRH</p>
                    </div>
                    <div class="content">
                        <p>Hola <strong>{ticket.name}</strong>,</p>
                        <p>Hemos recibido su solicitud de soporte y nuestro equipo está trabajando en ella.</p>
                        
                        <div class="ticket-box">
                            <p style="margin: 0 0 10px 0; color: #6b7280;">Su número de ticket es:</p>
                            <div class="ticket-id">{ticket_id}</div>
                        </div>
                        
                        <div class="info">
                            <strong>📋 Resumen de su solicitud:</strong><br><br>
                            <strong>Asunto:</strong> {ticket.subject}<br>
                            <strong>Categoría:</strong> {CATEGORY_LABELS.get(ticket.category, ticket.category)}<br>
                            <strong>Prioridad:</strong> {PRIORITY_LABELS.get(ticket.priority, ticket.priority)}
                        </div>
                        
                        <p style="margin-top: 20px;">
                            <strong>¿Qué sigue?</strong><br>
                            Nuestro equipo revisará su solicitud y le responderá a este correo electrónico. 
                            El tiempo de respuesta estimado depende de la prioridad de su caso.
                        </p>
                        
                        <p>Si tiene información adicional, puede responder directamente a este correo.</p>
                        
                        <p>Saludos cordiales,<br>
                        <strong>El Equipo de Soporte de FortexaRH</strong></p>
                    </div>
                    <div class="footer">
                        <p>FortexaRH - Sistema de RRHH y Nómina</p>
                        <p>Santo Domingo, República Dominicana</p>
                        <p><a href="https://fortexarh.com" style="color: #10b981;">www.fortexarh.com</a></p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            resend.Emails.send({
                "from": f"FortexaRH Soporte <{SENDER_EMAIL}>",
                "to": [ticket.email],
                "subject": f"Ticket #{ticket_id} - Hemos recibido su solicitud",
                "html": customer_email_html
            })
        except Exception as e:
            print(f"Error sending customer confirmation email: {e}")
        
        return SupportTicketResponse(
            ticket_id=ticket_id,
            message="Solicitud de soporte creada exitosamente",
            status="open"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear ticket: {str(e)}")


@router.get("/tickets")
async def get_support_tickets(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50
):
    """
    Get support tickets (for admin dashboard)
    """
    if db is None:
        return {"tickets": [], "total": 0}
    
    query = {}
    if status:
        query["status"] = status
    if priority:
        query["priority"] = priority
    
    tickets = await db.support_tickets.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    total = await db.support_tickets.count_documents(query)
    
    return {
        "tickets": tickets,
        "total": total
    }


@router.get("/tickets/{ticket_id}")
async def get_ticket_detail(ticket_id: str):
    """
    Get a specific support ticket by ID
    """
    if db is None:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    
    ticket = await db.support_tickets.find_one(
        {"ticket_id": ticket_id},
        {"_id": 0}
    )
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    
    return ticket


@router.patch("/tickets/{ticket_id}/status")
async def update_ticket_status(ticket_id: str, status: str):
    """
    Update ticket status (open, in_progress, resolved, closed)
    """
    if db is None:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    
    valid_statuses = ["open", "in_progress", "resolved", "closed"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Estado inválido. Use: {valid_statuses}")
    
    result = await db.support_tickets.update_one(
        {"ticket_id": ticket_id},
        {
            "$set": {
                "status": status,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    
    return {"message": f"Ticket actualizado a estado: {status}", "ticket_id": ticket_id}
