"""
Geo Alerts Service for Geolocation Attendance
Servicio de alertas automáticas por email
"""
import os
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Email service integration
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")


async def send_email_alert(
    to_emails: List[str],
    subject: str,
    html_content: str,
    from_email: str = "FortexaRH <alertas@fortexarh.com>"
) -> bool:
    """Send email alert using Resend"""
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not configured, skipping email alert")
        return False
    
    try:
        import resend
        resend.api_key = RESEND_API_KEY
        
        resend.Emails.send({
            "from": from_email,
            "to": to_emails,
            "subject": subject,
            "html": html_content
        })
        
        logger.info(f"Email alert sent to {to_emails}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email alert: {e}")
        return False


def build_outside_zone_email(
    employee_name: str,
    mark_data: Dict,
    company_name: str = "Su Empresa"
) -> Dict[str, str]:
    """Build email content for outside zone alert"""
    
    timestamp = mark_data.get("timestamp", "")
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        formatted_time = dt.strftime("%d/%m/%Y %H:%M")
    except:
        formatted_time = timestamp
    
    distance = mark_data.get("distance_to_zone", 0)
    location = mark_data.get("location_name", "Desconocido")
    mark_type = "Entrada" if mark_data.get("mark_type") == "entry" else "Salida"
    
    subject = f"⚠️ Alerta: {employee_name} marcó fuera de zona"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #f59e0b; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f8fafc; padding: 20px; border: 1px solid #e2e8f0; }}
            .footer {{ background: #1e293b; color: #94a3b8; padding: 15px; font-size: 12px; border-radius: 0 0 8px 8px; }}
            .alert-box {{ background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 15px 0; }}
            .data-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e2e8f0; }}
            .label {{ color: #64748b; }}
            .value {{ font-weight: bold; }}
            .btn {{ display: inline-block; background: #3b82f6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2 style="margin: 0;">⚠️ Alerta de Asistencia</h2>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">Marcación fuera de zona detectada</p>
            </div>
            <div class="content">
                <div class="alert-box">
                    <strong>{employee_name}</strong> ha registrado una marcación de <strong>{mark_type.lower()}</strong> 
                    fuera de las zonas autorizadas.
                </div>
                
                <h3 style="color: #1e293b; border-bottom: 2px solid #3b82f6; padding-bottom: 10px;">
                    Detalles de la Marcación
                </h3>
                
                <div class="data-row">
                    <span class="label">Empleado</span>
                    <span class="value">{employee_name}</span>
                </div>
                <div class="data-row">
                    <span class="label">Tipo</span>
                    <span class="value">{mark_type}</span>
                </div>
                <div class="data-row">
                    <span class="label">Fecha y Hora</span>
                    <span class="value">{formatted_time}</span>
                </div>
                <div class="data-row">
                    <span class="label">Ubicación más cercana</span>
                    <span class="value">{location}</span>
                </div>
                <div class="data-row">
                    <span class="label">Distancia a zona autorizada</span>
                    <span class="value" style="color: #dc2626;">{round(distance, 0)} metros</span>
                </div>
                <div class="data-row">
                    <span class="label">Coordenadas</span>
                    <span class="value">{mark_data.get('latitude', 0):.6f}, {mark_data.get('longitude', 0):.6f}</span>
                </div>
                
                <p style="margin-top: 20px; color: #64748b;">
                    Esta marcación requiere revisión manual. Puede aprobarla o rechazarla desde el panel de administración.
                </p>
                
                <a href="#" class="btn">Ver en Panel de Administración</a>
            </div>
            <div class="footer">
                <p>Este es un mensaje automático de FortexaRH - Sistema de RRHH y Nómina</p>
                <p>© 2026 {company_name}. Todos los derechos reservados.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return {"subject": subject, "html": html}


def build_fraud_alert_email(
    employee_name: str,
    fraud_alerts: List[Dict],
    mark_data: Dict,
    company_name: str = "Su Empresa"
) -> Dict[str, str]:
    """Build email content for fraud detection alert"""
    
    # Get highest priority alert
    highest_level = "low"
    for alert in fraud_alerts:
        level = alert.get("level", "low")
        if level == "critical":
            highest_level = "critical"
            break
        elif level == "high" and highest_level not in ["critical"]:
            highest_level = "high"
        elif level == "medium" and highest_level not in ["critical", "high"]:
            highest_level = "medium"
    
    level_colors = {
        "critical": "#dc2626",
        "high": "#ea580c",
        "medium": "#f59e0b",
        "low": "#3b82f6"
    }
    
    level_labels = {
        "critical": "CRÍTICA",
        "high": "ALTA",
        "medium": "MEDIA",
        "low": "BAJA"
    }
    
    color = level_colors.get(highest_level, "#3b82f6")
    level_label = level_labels.get(highest_level, "BAJA")
    
    subject = f"🚨 Alerta de Fraude ({level_label}): {employee_name}"
    
    alerts_html = ""
    for alert in fraud_alerts:
        alert_color = level_colors.get(alert.get("level", "low"), "#3b82f6")
        alerts_html += f"""
        <div style="background: #fff; border-left: 4px solid {alert_color}; padding: 12px; margin: 10px 0; border-radius: 0 4px 4px 0;">
            <strong style="color: {alert_color};">{level_labels.get(alert.get('level', 'low'), 'BAJA')}</strong>
            <p style="margin: 5px 0 0 0; color: #334155;">{alert.get('message', 'Alerta detectada')}</p>
        </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: {color}; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f8fafc; padding: 20px; border: 1px solid #e2e8f0; }}
            .footer {{ background: #1e293b; color: #94a3b8; padding: 15px; font-size: 12px; border-radius: 0 0 8px 8px; }}
            .btn {{ display: inline-block; background: #3b82f6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2 style="margin: 0;">🚨 Alerta de Fraude Detectada</h2>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">Prioridad: {level_label}</p>
            </div>
            <div class="content">
                <p>Se han detectado <strong>{len(fraud_alerts)} alerta(s)</strong> sospechosa(s) para el empleado <strong>{employee_name}</strong>:</p>
                
                {alerts_html}
                
                <h3 style="color: #1e293b; border-bottom: 2px solid {color}; padding-bottom: 10px; margin-top: 25px;">
                    Información de la Marcación
                </h3>
                
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="border-bottom: 1px solid #e2e8f0;">
                        <td style="padding: 8px 0; color: #64748b;">Fecha</td>
                        <td style="padding: 8px 0; font-weight: bold;">{mark_data.get('date', 'N/A')}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #e2e8f0;">
                        <td style="padding: 8px 0; color: #64748b;">Hora</td>
                        <td style="padding: 8px 0; font-weight: bold;">{mark_data.get('timestamp', 'N/A')[:19]}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #e2e8f0;">
                        <td style="padding: 8px 0; color: #64748b;">Ubicación</td>
                        <td style="padding: 8px 0; font-weight: bold;">{mark_data.get('location_name', 'Desconocido')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #64748b;">Coordenadas</td>
                        <td style="padding: 8px 0; font-weight: bold;">{mark_data.get('latitude', 0):.6f}, {mark_data.get('longitude', 0):.6f}</td>
                    </tr>
                </table>
                
                <p style="margin-top: 20px; color: #64748b;">
                    Se recomienda revisar esta marcación y tomar las acciones correspondientes según las políticas de la empresa.
                </p>
                
                <a href="#" class="btn">Revisar en Panel de Administración</a>
            </div>
            <div class="footer">
                <p>Este es un mensaje automático de FortexaRH - Sistema de RRHH y Nómina</p>
                <p>© 2026 {company_name}. Todos los derechos reservados.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return {"subject": subject, "html": html}


def build_daily_summary_email(
    summary_data: Dict,
    company_name: str = "Su Empresa",
    date: str = None
) -> Dict[str, str]:
    """Build email content for daily summary"""
    
    if not date:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    total_marks = summary_data.get("total_marks", 0)
    outside_zone = summary_data.get("outside_zone", 0)
    fraud_alerts = summary_data.get("fraud_alerts", 0)
    employees_marked = summary_data.get("employees_marked", 0)
    employees_pending = summary_data.get("employees_pending", 0)
    
    subject = f"📊 Resumen Diario de Asistencia GPS - {date}"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #3b82f6, #1d4ed8); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f8fafc; padding: 20px; border: 1px solid #e2e8f0; }}
            .footer {{ background: #1e293b; color: #94a3b8; padding: 15px; font-size: 12px; border-radius: 0 0 8px 8px; }}
            .stat-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin: 20px 0; }}
            .stat-box {{ background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
            .stat-value {{ font-size: 28px; font-weight: bold; }}
            .stat-label {{ font-size: 12px; color: #64748b; text-transform: uppercase; }}
            .btn {{ display: inline-block; background: #3b82f6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2 style="margin: 0;">📊 Resumen Diario de Asistencia</h2>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">{date}</p>
            </div>
            <div class="content">
                <div class="stat-grid">
                    <div class="stat-box">
                        <div class="stat-value" style="color: #10b981;">{employees_marked}</div>
                        <div class="stat-label">Empleados Marcaron</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value" style="color: #f59e0b;">{employees_pending}</div>
                        <div class="stat-label">Sin Marcar</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value" style="color: #3b82f6;">{total_marks}</div>
                        <div class="stat-label">Total Marcaciones</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value" style="color: #dc2626;">{fraud_alerts}</div>
                        <div class="stat-label">Alertas de Fraude</div>
                    </div>
                </div>
                
                <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; border-radius: 0 4px 4px 0;">
                    <strong>Marcaciones fuera de zona:</strong> {outside_zone}
                </div>
                
                <p style="color: #64748b;">
                    Este es un resumen automático de la actividad de asistencia GPS del día. 
                    Para más detalles, acceda al panel de administración.
                </p>
                
                <a href="#" class="btn">Ver Detalle Completo</a>
            </div>
            <div class="footer">
                <p>Este es un mensaje automático de FortexaRH - Sistema de RRHH y Nómina</p>
                <p>© 2026 {company_name}. Todos los derechos reservados.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return {"subject": subject, "html": html}


async def send_outside_zone_alert(
    employee_name: str,
    mark_data: Dict,
    recipient_emails: List[str],
    company_name: str = "Su Empresa"
) -> bool:
    """Send alert email for outside zone marking"""
    if not recipient_emails:
        return False
    
    email_content = build_outside_zone_email(employee_name, mark_data, company_name)
    return await send_email_alert(
        to_emails=recipient_emails,
        subject=email_content["subject"],
        html_content=email_content["html"]
    )


async def send_fraud_alert(
    employee_name: str,
    fraud_alerts: List[Dict],
    mark_data: Dict,
    recipient_emails: List[str],
    company_name: str = "Su Empresa"
) -> bool:
    """Send alert email for detected fraud"""
    if not recipient_emails or not fraud_alerts:
        return False
    
    # Only send for medium, high, or critical alerts
    significant_alerts = [a for a in fraud_alerts if a.get("level") in ["medium", "high", "critical"]]
    
    if not significant_alerts:
        return False
    
    email_content = build_fraud_alert_email(employee_name, significant_alerts, mark_data, company_name)
    return await send_email_alert(
        to_emails=recipient_emails,
        subject=email_content["subject"],
        html_content=email_content["html"]
    )


async def send_daily_summary(
    summary_data: Dict,
    recipient_emails: List[str],
    company_name: str = "Su Empresa",
    date: str = None
) -> bool:
    """Send daily summary email"""
    if not recipient_emails:
        return False
    
    email_content = build_daily_summary_email(summary_data, company_name, date)
    return await send_email_alert(
        to_emails=recipient_emails,
        subject=email_content["subject"],
        html_content=email_content["html"]
    )
