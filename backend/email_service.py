"""
Email service module for FortexaRH
Uses Resend API for transactional emails
"""
import os
import asyncio
import logging
import resend
from datetime import datetime

# Configure Resend
resend.api_key = os.environ.get('RESEND_API_KEY')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'noreply@fortexaerp.com')
INFO_EMAIL = os.environ.get('INFO_EMAIL', 'info@fortexaerp.com')

logger = logging.getLogger(__name__)

def get_email_header():
    """Common email header with logo"""
    return """
    <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
        <h1 style="color: white; margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 28px;">
            FortexaRH
        </h1>
        <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0; font-size: 14px;">
            Sistema de Recursos Humanos y Nómina
        </p>
    </div>
    """

def get_email_footer():
    """Common email footer"""
    return """
    <div style="background: #f8fafc; padding: 20px; text-align: center; border-top: 1px solid #e2e8f0;">
        <p style="color: #64748b; font-size: 12px; margin: 0 0 10px 0;">
            © 2025 FortexaRH. Todos los derechos reservados.
        </p>
        <p style="color: #94a3b8; font-size: 11px; margin: 0;">
            Av. Winston Churchill, Santo Domingo, República Dominicana<br>
            Tel: (809) 685-9898 | Email: info@fortexaerp.com
        </p>
    </div>
    """

async def send_payment_confirmation_email(
    recipient_email: str,
    recipient_name: str,
    plan_name: str,
    amount: float,
    employee_count: int,
    invoice_number: str,
    period_start: str,
    period_end: str
):
    """Send payment confirmation email after successful payment"""
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; background-color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            {get_email_header()}
            
            <div style="background: white; padding: 30px; border-radius: 0 0 8px 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <div style="text-align: center; margin-bottom: 30px;">
                    <div style="width: 60px; height: 60px; background: #dcfce7; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 15px;">
                        <span style="font-size: 30px;">✓</span>
                    </div>
                    <h2 style="color: #1e293b; margin: 0; font-size: 24px;">¡Pago Confirmado!</h2>
                </div>
                
                <p style="color: #475569; font-size: 16px; line-height: 1.6;">
                    Hola <strong>{recipient_name}</strong>,
                </p>
                
                <p style="color: #475569; font-size: 16px; line-height: 1.6;">
                    Hemos recibido tu pago exitosamente. A continuación los detalles de tu suscripción:
                </p>
                
                <div style="background: #f8fafc; border-radius: 8px; padding: 20px; margin: 25px 0;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 10px 0; color: #64748b; font-size: 14px;">Factura No.</td>
                            <td style="padding: 10px 0; color: #1e293b; font-size: 14px; text-align: right; font-weight: 600;">{invoice_number}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px 0; color: #64748b; font-size: 14px;">Plan</td>
                            <td style="padding: 10px 0; color: #1e293b; font-size: 14px; text-align: right; font-weight: 600;">{plan_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px 0; color: #64748b; font-size: 14px;">Empleados</td>
                            <td style="padding: 10px 0; color: #1e293b; font-size: 14px; text-align: right; font-weight: 600;">{employee_count}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px 0; color: #64748b; font-size: 14px;">Período</td>
                            <td style="padding: 10px 0; color: #1e293b; font-size: 14px; text-align: right;">{period_start} - {period_end}</td>
                        </tr>
                        <tr style="border-top: 2px solid #e2e8f0;">
                            <td style="padding: 15px 0 10px 0; color: #1e293b; font-size: 16px; font-weight: 600;">Total Pagado</td>
                            <td style="padding: 15px 0 10px 0; color: #10b981; font-size: 20px; text-align: right; font-weight: 700;">${amount:.2f} USD</td>
                        </tr>
                    </table>
                </div>
                
                <p style="color: #475569; font-size: 14px; line-height: 1.6;">
                    Tu suscripción está activa y tienes acceso a todas las funciones de tu plan.
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://fortexaerp.com/dashboard" style="display: inline-block; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 14px 30px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                        Ir al Dashboard
                    </a>
                </div>
                
                <p style="color: #94a3b8; font-size: 13px; line-height: 1.6; margin-top: 30px;">
                    Si tienes alguna pregunta sobre tu suscripción, no dudes en contactarnos respondiendo a este correo o llamando al (809) 685-9898.
                </p>
            </div>
            
            {get_email_footer()}
        </div>
    </body>
    </html>
    """
    
    params = {
        "from": f"FortexaRH <{SENDER_EMAIL}>",
        "to": [recipient_email],
        "subject": f"✓ Pago Confirmado - {plan_name} | FortexaRH",
        "html": html_content
    }
    
    try:
        email = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Payment confirmation email sent to {recipient_email}, email_id: {email.get('id')}")
        return {"status": "success", "email_id": email.get("id")}
    except Exception as e:
        logger.error(f"Failed to send payment confirmation email to {recipient_email}: {str(e)}")
        return {"status": "error", "error": str(e)}


async def send_welcome_email(
    recipient_email: str,
    recipient_name: str,
    company_name: str,
    plan_name: str = "Prueba Gratuita"
):
    """Send welcome email after registration"""
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; background-color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            {get_email_header()}
            
            <div style="background: white; padding: 30px; border-radius: 0 0 8px 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <div style="text-align: center; margin-bottom: 30px;">
                    <div style="width: 60px; height: 60px; background: #dbeafe; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 15px;">
                        <span style="font-size: 30px;">🎉</span>
                    </div>
                    <h2 style="color: #1e293b; margin: 0; font-size: 24px;">¡Bienvenido a FortexaRH!</h2>
                </div>
                
                <p style="color: #475569; font-size: 16px; line-height: 1.6;">
                    Hola <strong>{recipient_name}</strong>,
                </p>
                
                <p style="color: #475569; font-size: 16px; line-height: 1.6;">
                    Tu cuenta para <strong>{company_name}</strong> ha sido creada exitosamente. Estamos emocionados de tenerte como parte de nuestra comunidad.
                </p>
                
                <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border-radius: 8px; padding: 20px; margin: 25px 0; border-left: 4px solid #3b82f6;">
                    <p style="color: #1e40af; font-size: 14px; margin: 0;">
                        <strong>Tu plan actual:</strong> {plan_name}
                    </p>
                </div>
                
                <h3 style="color: #1e293b; font-size: 18px; margin-top: 30px;">Primeros pasos:</h3>
                
                <div style="margin: 20px 0;">
                    <div style="display: flex; align-items: flex-start; margin-bottom: 15px;">
                        <div style="width: 28px; height: 28px; background: #10b981; border-radius: 50%; color: white; text-align: center; line-height: 28px; font-size: 14px; font-weight: 600; margin-right: 12px; flex-shrink: 0;">1</div>
                        <div>
                            <strong style="color: #1e293b;">Configura tu empresa</strong>
                            <p style="color: #64748b; font-size: 14px; margin: 5px 0 0 0;">Agrega el logo y datos de tu empresa</p>
                        </div>
                    </div>
                    <div style="display: flex; align-items: flex-start; margin-bottom: 15px;">
                        <div style="width: 28px; height: 28px; background: #10b981; border-radius: 50%; color: white; text-align: center; line-height: 28px; font-size: 14px; font-weight: 600; margin-right: 12px; flex-shrink: 0;">2</div>
                        <div>
                            <strong style="color: #1e293b;">Agrega empleados</strong>
                            <p style="color: #64748b; font-size: 14px; margin: 5px 0 0 0;">Registra a tu equipo en el sistema</p>
                        </div>
                    </div>
                    <div style="display: flex; align-items: flex-start;">
                        <div style="width: 28px; height: 28px; background: #10b981; border-radius: 50%; color: white; text-align: center; line-height: 28px; font-size: 14px; font-weight: 600; margin-right: 12px; flex-shrink: 0;">3</div>
                        <div>
                            <strong style="color: #1e293b;">Genera tu primera nómina</strong>
                            <p style="color: #64748b; font-size: 14px; margin: 5px 0 0 0;">Usa nuestra calculadora de nómina</p>
                        </div>
                    </div>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://fortexaerp.com/dashboard" style="display: inline-block; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 14px 30px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                        Comenzar Ahora
                    </a>
                </div>
                
                <p style="color: #94a3b8; font-size: 13px; line-height: 1.6; margin-top: 30px;">
                    ¿Necesitas ayuda? Nuestro equipo de soporte está disponible de Lunes a Viernes, 9AM - 4PM. Contáctanos en info@fortexaerp.com o al (809) 685-9898.
                </p>
            </div>
            
            {get_email_footer()}
        </div>
    </body>
    </html>
    """
    
    params = {
        "from": f"FortexaRH <{SENDER_EMAIL}>",
        "to": [recipient_email],
        "subject": f"🎉 ¡Bienvenido a FortexaRH, {recipient_name}!",
        "html": html_content
    }
    
    try:
        email = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Welcome email sent to {recipient_email}, email_id: {email.get('id')}")
        return {"status": "success", "email_id": email.get("id")}
    except Exception as e:
        logger.error(f"Failed to send welcome email to {recipient_email}: {str(e)}")
        return {"status": "error", "error": str(e)}


async def send_invoice_email(
    recipient_email: str,
    recipient_name: str,
    company_name: str,
    invoice_number: str,
    plan_name: str,
    base_price: float,
    employee_count: int,
    price_per_employee: float,
    total: float,
    period_start: str,
    period_end: str,
    paid_at: str
):
    """Send invoice email with detailed breakdown"""
    
    employee_cost = employee_count * price_per_employee
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; background-color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            {get_email_header()}
            
            <div style="background: white; padding: 30px; border-radius: 0 0 8px 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 30px; flex-wrap: wrap;">
                    <div>
                        <h2 style="color: #1e293b; margin: 0 0 5px 0; font-size: 24px;">Factura</h2>
                        <p style="color: #64748b; margin: 0; font-size: 14px;">No. {invoice_number}</p>
                    </div>
                    <div style="text-align: right;">
                        <span style="display: inline-block; background: #dcfce7; color: #166534; padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;">
                            ✓ PAGADA
                        </span>
                        <p style="color: #64748b; margin: 10px 0 0 0; font-size: 13px;">Fecha: {paid_at}</p>
                    </div>
                </div>
                
                <div style="background: #f8fafc; border-radius: 8px; padding: 20px; margin-bottom: 25px;">
                    <p style="color: #64748b; font-size: 12px; margin: 0 0 5px 0; text-transform: uppercase;">Facturado a:</p>
                    <p style="color: #1e293b; font-size: 16px; font-weight: 600; margin: 0;">{company_name}</p>
                    <p style="color: #64748b; font-size: 14px; margin: 5px 0 0 0;">{recipient_name}</p>
                    <p style="color: #64748b; font-size: 14px; margin: 3px 0 0 0;">{recipient_email}</p>
                </div>
                
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <thead>
                        <tr style="border-bottom: 2px solid #e2e8f0;">
                            <th style="text-align: left; padding: 12px 0; color: #64748b; font-size: 12px; text-transform: uppercase;">Descripción</th>
                            <th style="text-align: center; padding: 12px 0; color: #64748b; font-size: 12px; text-transform: uppercase;">Cant.</th>
                            <th style="text-align: right; padding: 12px 0; color: #64748b; font-size: 12px; text-transform: uppercase;">Precio</th>
                            <th style="text-align: right; padding: 12px 0; color: #64748b; font-size: 12px; text-transform: uppercase;">Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr style="border-bottom: 1px solid #e2e8f0;">
                            <td style="padding: 15px 0; color: #1e293b; font-size: 14px;">
                                <strong>{plan_name}</strong><br>
                                <span style="color: #64748b; font-size: 12px;">Suscripción mensual base</span>
                            </td>
                            <td style="padding: 15px 0; color: #1e293b; font-size: 14px; text-align: center;">1</td>
                            <td style="padding: 15px 0; color: #1e293b; font-size: 14px; text-align: right;">${base_price:.2f}</td>
                            <td style="padding: 15px 0; color: #1e293b; font-size: 14px; text-align: right;">${base_price:.2f}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #e2e8f0;">
                            <td style="padding: 15px 0; color: #1e293b; font-size: 14px;">
                                <strong>Empleados adicionales</strong><br>
                                <span style="color: #64748b; font-size: 12px;">Costo por empleado</span>
                            </td>
                            <td style="padding: 15px 0; color: #1e293b; font-size: 14px; text-align: center;">{employee_count}</td>
                            <td style="padding: 15px 0; color: #1e293b; font-size: 14px; text-align: right;">${price_per_employee:.2f}</td>
                            <td style="padding: 15px 0; color: #1e293b; font-size: 14px; text-align: right;">${employee_cost:.2f}</td>
                        </tr>
                    </tbody>
                    <tfoot>
                        <tr>
                            <td colspan="3" style="padding: 15px 0; text-align: right; color: #64748b; font-size: 14px;">Subtotal</td>
                            <td style="padding: 15px 0; text-align: right; color: #1e293b; font-size: 14px;">${total:.2f}</td>
                        </tr>
                        <tr>
                            <td colspan="3" style="padding: 10px 0; text-align: right; color: #64748b; font-size: 14px;">ITBIS (0%)</td>
                            <td style="padding: 10px 0; text-align: right; color: #1e293b; font-size: 14px;">$0.00</td>
                        </tr>
                        <tr style="border-top: 2px solid #1e293b;">
                            <td colspan="3" style="padding: 15px 0; text-align: right; color: #1e293b; font-size: 18px; font-weight: 700;">Total USD</td>
                            <td style="padding: 15px 0; text-align: right; color: #10b981; font-size: 20px; font-weight: 700;">${total:.2f}</td>
                        </tr>
                    </tfoot>
                </table>
                
                <div style="background: #f0fdf4; border-radius: 8px; padding: 15px; margin-top: 20px; border-left: 4px solid #10b981;">
                    <p style="color: #166534; font-size: 14px; margin: 0;">
                        <strong>Período de servicio:</strong> {period_start} - {period_end}
                    </p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://fortexaerp.com/subscriptions" style="display: inline-block; background: #f1f5f9; color: #475569; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: 500; font-size: 14px;">
                        Ver Historial de Facturas
                    </a>
                </div>
                
                <p style="color: #94a3b8; font-size: 12px; line-height: 1.6; margin-top: 30px; text-align: center;">
                    Esta factura fue generada automáticamente y es válida sin firma ni sello.<br>
                    Para cualquier consulta, contacte a info@fortexaerp.com
                </p>
            </div>
            
            {get_email_footer()}
        </div>
    </body>
    </html>
    """
    
    params = {
        "from": f"FortexaRH Facturación <{SENDER_EMAIL}>",
        "to": [recipient_email],
        "subject": f"Factura {invoice_number} - FortexaRH",
        "html": html_content
    }
    
    try:
        email = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Invoice email sent to {recipient_email}, email_id: {email.get('id')}")
        return {"status": "success", "email_id": email.get("id")}
    except Exception as e:
        logger.error(f"Failed to send invoice email to {recipient_email}: {str(e)}")
        return {"status": "error", "error": str(e)}
