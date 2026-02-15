"""
Notifications Routes - FortexaRH
Handles payroll reminders, birthday notifications, and notification settings
"""
from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import uuid
import asyncio
import os
import resend
import logging

router = APIRouter(prefix="/notification-settings", tags=["Notification Settings"])
security = HTTPBearer(auto_error=False)

db = None
_get_current_user_func = None

logger = logging.getLogger(__name__)

# Configure Resend
resend.api_key = os.environ.get('RESEND_API_KEY')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'noreply@fortexarh.com')


def init_router(database, auth_func):
    global db, _get_current_user_func
    db = database
    _get_current_user_func = auth_func


async def get_current_user(request: Request, credentials=Depends(security)):
    """Wrapper for the injected auth function"""
    if _get_current_user_func is None:
        raise HTTPException(status_code=500, detail="Auth not initialized")
    return await _get_current_user_func(request, credentials)


# ==================== MODELS ====================
from models.system import NotificationSettings, PayrollDateConfig


# ==================== EMAIL TEMPLATES ====================

def get_email_header():
    return """
    <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
        <h1 style="color: white; margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 28px;">
            FortexaRH
        </h1>
    </div>
    """


def get_email_footer():
    return """
    <div style="background: #f8fafc; padding: 20px; text-align: center; border-top: 1px solid #e2e8f0;">
        <p style="color: #64748b; font-size: 12px; margin: 0;">
            © 2025 FortexaRH. Todos los derechos reservados.
        </p>
    </div>
    """


async def send_payroll_reminder_email(
    recipient_email: str,
    recipient_name: str,
    company_name: str,
    payroll_date: str,
    days_until: int,
    employee_count: int,
    estimated_total: float
):
    """Send payroll reminder email"""
    
    urgency_color = "#dc2626" if days_until <= 1 else "#f59e0b" if days_until <= 3 else "#10b981"
    urgency_text = "¡HOY!" if days_until == 0 else f"en {days_until} día{'s' if days_until > 1 else ''}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="margin: 0; padding: 0; background-color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            {get_email_header()}
            
            <div style="background: white; padding: 30px; border-radius: 0 0 8px 8px;">
                <div style="text-align: center; margin-bottom: 25px;">
                    <div style="width: 60px; height: 60px; background: #fef3c7; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 15px;">
                        <span style="font-size: 30px;">⏰</span>
                    </div>
                    <h2 style="color: #1e293b; margin: 0; font-size: 22px;">Recordatorio de Nómina</h2>
                </div>
                
                <p style="color: #475569; font-size: 16px;">Hola <strong>{recipient_name}</strong>,</p>
                
                <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border-radius: 12px; padding: 20px; margin: 20px 0; text-align: center;">
                    <p style="color: #92400e; font-size: 14px; margin: 0 0 5px 0;">Fecha de pago de nómina</p>
                    <p style="color: {urgency_color}; font-size: 28px; font-weight: 700; margin: 0;">{urgency_text}</p>
                    <p style="color: #78350f; font-size: 16px; margin: 10px 0 0 0;">{payroll_date}</p>
                </div>
                
                <div style="background: #f8fafc; border-radius: 8px; padding: 20px; margin: 20px 0;">
                    <h3 style="color: #1e293b; font-size: 16px; margin: 0 0 15px 0;">Resumen de la Nómina</h3>
                    <table style="width: 100%;">
                        <tr>
                            <td style="color: #64748b; padding: 8px 0;">Empleados a pagar:</td>
                            <td style="color: #1e293b; font-weight: 600; text-align: right;">{employee_count}</td>
                        </tr>
                        <tr>
                            <td style="color: #64748b; padding: 8px 0;">Total estimado:</td>
                            <td style="color: #10b981; font-weight: 700; font-size: 18px; text-align: right;">RD$ {estimated_total:,.2f}</td>
                        </tr>
                    </table>
                </div>
                
                <div style="text-align: center; margin: 25px 0;">
                    <a href="https://fortexarh.com/payroll" style="display: inline-block; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 14px 30px; text-decoration: none; border-radius: 8px; font-weight: 600;">
                        Ir a Nómina
                    </a>
                </div>
                
                <p style="color: #94a3b8; font-size: 13px; text-align: center;">
                    Recuerda revisar y aprobar la nómina antes de la fecha de pago.
                </p>
            </div>
            
            {get_email_footer()}
        </div>
    </body>
    </html>
    """
    
    try:
        params = {
            "from": f"FortexaRH <{SENDER_EMAIL}>",
            "to": [recipient_email],
            "subject": f"⏰ Recordatorio: Nómina {urgency_text} - {company_name}",
            "html": html_content
        }
        email = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Payroll reminder sent to {recipient_email}")
        return {"status": "success", "email_id": email.get("id")}
    except Exception as e:
        logger.error(f"Failed to send payroll reminder: {str(e)}")
        return {"status": "error", "error": str(e)}


async def send_birthday_notification_email(
    recipient_email: str,
    recipient_name: str,
    company_name: str,
    birthdays: List[dict]
):
    """Send birthday notification email to HR/Admin"""
    
    birthday_list = ""
    for emp in birthdays:
        birthday_list += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #e2e8f0;">
                <strong style="color: #1e293b;">{emp['name']}</strong><br>
                <span style="color: #64748b; font-size: 13px;">{emp['department']} - {emp['position']}</span>
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #e2e8f0; text-align: right;">
                <span style="background: #fef3c7; color: #92400e; padding: 4px 12px; border-radius: 20px; font-size: 13px;">
                    🎂 {emp['date']}
                </span>
            </td>
        </tr>
        """
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="margin: 0; padding: 0; background-color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            {get_email_header()}
            
            <div style="background: white; padding: 30px; border-radius: 0 0 8px 8px;">
                <div style="text-align: center; margin-bottom: 25px;">
                    <div style="width: 60px; height: 60px; background: #fef3c7; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 15px;">
                        <span style="font-size: 30px;">🎉</span>
                    </div>
                    <h2 style="color: #1e293b; margin: 0; font-size: 22px;">¡Cumpleaños Próximos!</h2>
                </div>
                
                <p style="color: #475569; font-size: 16px;">Hola <strong>{recipient_name}</strong>,</p>
                
                <p style="color: #475569; font-size: 15px;">
                    Los siguientes empleados de <strong>{company_name}</strong> celebran su cumpleaños pronto:
                </p>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    {birthday_list}
                </table>
                
                <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border-radius: 8px; padding: 15px; margin: 20px 0;">
                    <p style="color: #1e40af; font-size: 14px; margin: 0;">
                        💡 <strong>Sugerencia:</strong> No olvides felicitar a tus empleados en su día especial. Un pequeño gesto puede hacer una gran diferencia.
                    </p>
                </div>
                
                <div style="text-align: center; margin: 25px 0;">
                    <a href="https://fortexarh.com/employees" style="display: inline-block; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 14px 30px; text-decoration: none; border-radius: 8px; font-weight: 600;">
                        Ver Empleados
                    </a>
                </div>
            </div>
            
            {get_email_footer()}
        </div>
    </body>
    </html>
    """
    
    count = len(birthdays)
    try:
        params = {
            "from": f"FortexaRH <{SENDER_EMAIL}>",
            "to": [recipient_email],
            "subject": f"🎂 {count} Cumpleaños{'s' if count > 1 else ''} Próximo{'s' if count > 1 else ''} - {company_name}",
            "html": html_content
        }
        email = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Birthday notification sent to {recipient_email}")
        return {"status": "success", "email_id": email.get("id")}
    except Exception as e:
        logger.error(f"Failed to send birthday notification: {str(e)}")
        return {"status": "error", "error": str(e)}


# ==================== ENDPOINTS ====================

@router.get("/settings")
async def get_notification_settings(current_user: dict = Depends(get_current_user)):
    """Get notification settings for the company"""
    company_id = current_user.get("company_id")
    
    settings = await db.notification_settings.find_one(
        {"company_id": company_id},
        {"_id": 0}
    )
    
    if not settings:
        # Return default settings
        return {
            "company_id": company_id,
            "payroll_reminder_enabled": True,
            "payroll_reminder_days": 3,
            "payroll_day": 15,
            "second_payroll_day": None,
            "birthday_notifications_enabled": True,
            "birthday_notification_days": 1,
            "contract_expiry_enabled": True,
            "contract_expiry_days": 30,
            "notification_emails": [current_user.get("email")]
        }
    
    return settings


@router.put("/settings")
async def update_notification_settings(
    settings: NotificationSettings,
    current_user: dict = Depends(get_current_user)
):
    """Update notification settings for the company"""
    if current_user.get("role") not in ["admin", "hr_manager"]:
        raise HTTPException(status_code=403, detail="No tienes permisos para modificar configuraciones")
    
    company_id = current_user.get("company_id")
    
    await db.notification_settings.update_one(
        {"company_id": company_id},
        {"$set": {
            **settings.dict(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": current_user.get("user_id")
        }},
        upsert=True
    )
    
    return {"message": "Configuración actualizada correctamente"}


@router.put("/payroll-dates")
async def update_payroll_dates(
    config: PayrollDateConfig,
    current_user: dict = Depends(get_current_user)
):
    """Update payroll dates configuration"""
    if current_user.get("role") not in ["admin", "hr_manager"]:
        raise HTTPException(status_code=403, detail="No tienes permisos para modificar configuraciones")
    
    company_id = current_user.get("company_id")
    
    await db.notification_settings.update_one(
        {"company_id": company_id},
        {"$set": {
            "payroll_day": config.payroll_day,
            "second_payroll_day": config.second_payroll_day,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    
    return {"message": "Fechas de nómina actualizadas"}


@router.get("/upcoming-birthdays")
async def get_upcoming_birthdays(
    days: int = 7,
    current_user: dict = Depends(get_current_user)
):
    """Get employees with upcoming birthdays"""
    company_id = current_user.get("company_id")
    today = datetime.now(timezone.utc)
    
    employees = await db.employees.find(
        {"company_id": company_id, "status": "active"},
        {"_id": 0, "employee_id": 1, "first_name": 1, "last_name": 1, "birth_date": 1, "department": 1, "position": 1}
    ).to_list(1000)
    
    upcoming = []
    for emp in employees:
        birth_date_str = emp.get("birth_date")
        if not birth_date_str:
            continue
        
        try:
            # Parse birth date
            if isinstance(birth_date_str, str):
                birth_date = datetime.fromisoformat(birth_date_str.replace("Z", "+00:00"))
            else:
                birth_date = birth_date_str
            
            # Calculate this year's birthday
            this_year_bday = birth_date.replace(year=today.year)
            if this_year_bday.tzinfo is None:
                this_year_bday = this_year_bday.replace(tzinfo=timezone.utc)
            
            # If birthday already passed this year, check next year
            if this_year_bday < today:
                this_year_bday = this_year_bday.replace(year=today.year + 1)
            
            days_until = (this_year_bday.date() - today.date()).days
            
            if 0 <= days_until <= days:
                upcoming.append({
                    "employee_id": emp["employee_id"],
                    "name": f"{emp['first_name']} {emp['last_name']}",
                    "department": emp.get("department", "Sin departamento"),
                    "position": emp.get("position", "Sin posición"),
                    "birth_date": birth_date.strftime("%d/%m"),
                    "days_until": days_until,
                    "is_today": days_until == 0
                })
        except Exception as e:
            logger.warning(f"Error parsing birth date for employee {emp.get('employee_id')}: {e}")
            continue
    
    # Sort by days until birthday
    upcoming.sort(key=lambda x: x["days_until"])
    
    return upcoming


@router.post("/send-payroll-reminder")
async def send_payroll_reminder(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Manually trigger payroll reminder"""
    if current_user.get("role") not in ["admin", "hr_manager"]:
        raise HTTPException(status_code=403, detail="No tienes permisos")
    
    company_id = current_user.get("company_id")
    
    # Get company info
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    # Get notification settings
    settings = await db.notification_settings.find_one({"company_id": company_id}, {"_id": 0})
    payroll_day = settings.get("payroll_day", 15) if settings else 15
    
    # Calculate next payroll date
    today = datetime.now(timezone.utc)
    if today.day > payroll_day:
        # Next month
        next_month = today.month + 1 if today.month < 12 else 1
        next_year = today.year if today.month < 12 else today.year + 1
        payroll_date = datetime(next_year, next_month, payroll_day, tzinfo=timezone.utc)
    else:
        payroll_date = datetime(today.year, today.month, payroll_day, tzinfo=timezone.utc)
    
    days_until = (payroll_date.date() - today.date()).days
    
    # Get employee count and estimated total
    employees = await db.employees.find(
        {"company_id": company_id, "status": "active"},
        {"_id": 0, "salary": 1}
    ).to_list(1000)
    
    employee_count = len(employees)
    estimated_total = sum(emp.get("salary", 0) for emp in employees)
    
    # Get admin users to notify
    admins = await db.users.find(
        {"company_id": company_id, "role": {"$in": ["admin", "hr_manager"]}},
        {"_id": 0, "email": 1, "name": 1}
    ).to_list(10)
    
    # Send emails in background
    for admin in admins:
        background_tasks.add_task(
            send_payroll_reminder_email,
            admin["email"],
            admin["name"],
            company.get("name", "Tu Empresa"),
            payroll_date.strftime("%d de %B, %Y"),
            days_until,
            employee_count,
            estimated_total
        )
    
    # Log the notification
    await db.notification_logs.insert_one({
        "log_id": f"log_{uuid.uuid4().hex[:8]}",
        "company_id": company_id,
        "type": "payroll_reminder",
        "sent_to": [a["email"] for a in admins],
        "payroll_date": payroll_date.isoformat(),
        "days_until": days_until,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "message": f"Recordatorio enviado a {len(admins)} usuarios",
        "payroll_date": payroll_date.isoformat(),
        "days_until": days_until
    }


@router.post("/send-birthday-notifications")
async def send_birthday_notifications(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Manually trigger birthday notifications"""
    if current_user.get("role") not in ["admin", "hr_manager"]:
        raise HTTPException(status_code=403, detail="No tienes permisos")
    
    company_id = current_user.get("company_id")
    
    # Get company info
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    # Get upcoming birthdays (next 7 days)
    today = datetime.now(timezone.utc)
    employees = await db.employees.find(
        {"company_id": company_id, "status": "active"},
        {"_id": 0, "first_name": 1, "last_name": 1, "birth_date": 1, "department": 1, "position": 1}
    ).to_list(1000)
    
    upcoming_birthdays = []
    for emp in employees:
        birth_date_str = emp.get("birth_date")
        if not birth_date_str:
            continue
        
        try:
            if isinstance(birth_date_str, str):
                birth_date = datetime.fromisoformat(birth_date_str.replace("Z", "+00:00"))
            else:
                birth_date = birth_date_str
            
            this_year_bday = birth_date.replace(year=today.year)
            if this_year_bday.tzinfo is None:
                this_year_bday = this_year_bday.replace(tzinfo=timezone.utc)
            
            if this_year_bday < today:
                this_year_bday = this_year_bday.replace(year=today.year + 1)
            
            days_until = (this_year_bday.date() - today.date()).days
            
            if 0 <= days_until <= 7:
                date_str = "Hoy" if days_until == 0 else f"En {days_until} día{'s' if days_until > 1 else ''}"
                upcoming_birthdays.append({
                    "name": f"{emp['first_name']} {emp['last_name']}",
                    "department": emp.get("department", "Sin departamento"),
                    "position": emp.get("position", "Sin posición"),
                    "date": date_str
                })
        except Exception:
            continue
    
    if not upcoming_birthdays:
        return {"message": "No hay cumpleaños próximos", "count": 0}
    
    # Get admin users to notify
    admins = await db.users.find(
        {"company_id": company_id, "role": {"$in": ["admin", "hr_manager"]}},
        {"_id": 0, "email": 1, "name": 1}
    ).to_list(10)
    
    # Send emails in background
    for admin in admins:
        background_tasks.add_task(
            send_birthday_notification_email,
            admin["email"],
            admin["name"],
            company.get("name", "Tu Empresa"),
            upcoming_birthdays
        )
    
    # Log the notification
    await db.notification_logs.insert_one({
        "log_id": f"log_{uuid.uuid4().hex[:8]}",
        "company_id": company_id,
        "type": "birthday_notification",
        "sent_to": [a["email"] for a in admins],
        "birthdays": [b["name"] for b in upcoming_birthdays],
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "message": f"Notificación enviada a {len(admins)} usuarios",
        "birthdays_count": len(upcoming_birthdays)
    }


@router.get("/logs")
async def get_notification_logs(
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Get notification history"""
    company_id = current_user.get("company_id")
    
    logs = await db.notification_logs.find(
        {"company_id": company_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return logs
