"""
QuickBooks Online Integration Router
OAuth2 authentication and data synchronization with QuickBooks Online
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Callable, Optional, Dict, List, Any
from datetime import datetime, timezone, timedelta
import httpx
import secrets
import base64
import os

router = APIRouter(prefix="/quickbooks", tags=["QuickBooks Integration"])
from config import db
from utils.auth import get_current_user
security = HTTPBearer(auto_error=False)

# QuickBooks Configuration
QB_CLIENT_ID = os.environ.get('QUICKBOOKS_CLIENT_ID', '')
QB_CLIENT_SECRET = os.environ.get('QUICKBOOKS_CLIENT_SECRET', '')
QB_REDIRECT_URI = os.environ.get('QUICKBOOKS_REDIRECT_URI', '')
QB_AUTHORIZATION_URL = "https://appcenter.intuit.com/connect/oauth2"
QB_TOKEN_ENDPOINT = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
QB_REVOKE_ENDPOINT = "https://developer.api.intuit.com/v2/oauth2/tokens/revoke"
QB_API_BASE_URL = "https://quickbooks.api.intuit.com/v3/company"

# For sandbox/development
QB_SANDBOX_API_URL = "https://sandbox-quickbooks.api.intuit.com/v3/company"


# ============== MODELS ==============
from models.system import QuickBooksConnection, QuickBooksSyncRequest as SyncRequest


# ============== HELPER FUNCTIONS ==============

def get_auth_header():
    """Generate Base64 encoded authorization header"""
    credentials = base64.b64encode(
        f"{QB_CLIENT_ID}:{QB_CLIENT_SECRET}".encode()
    ).decode()
    return f"Basic {credentials}"


async def refresh_access_token(refresh_token: str) -> Dict:
    """Refresh the QuickBooks access token"""
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": get_auth_header(),
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        
        response = await client.post(
            QB_TOKEN_ENDPOINT,
            headers=headers,
            data=data
        )
        
        if response.status_code != 200:
            raise Exception(f"Token refresh failed: {response.text}")
        
        return response.json()


async def get_valid_token(company_id: str, user_id: str) -> Optional[str]:
    """Get a valid access token, refreshing if necessary"""
    connection = await db.quickbooks_connections.find_one({
        "company_id": company_id,
        "user_id": user_id,
        "is_active": True
    })
    
    if not connection:
        return None
    
    expires_at = connection.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    
    # Check if token is about to expire (within 15 minutes)
    if expires_at < datetime.now(timezone.utc) + timedelta(minutes=15):
        try:
            new_tokens = await refresh_access_token(connection["refresh_token"])
            
            # Update connection with new tokens
            await db.quickbooks_connections.update_one(
                {"_id": connection["_id"]},
                {"$set": {
                    "access_token": new_tokens["access_token"],
                    "refresh_token": new_tokens.get("refresh_token", connection["refresh_token"]),
                    "expires_at": datetime.now(timezone.utc) + timedelta(seconds=new_tokens["expires_in"]),
                    "updated_at": datetime.now(timezone.utc)
                }}
            )
            
            return new_tokens["access_token"]
        except Exception as e:
            print(f"Token refresh failed: {e}")
            return None
    
    return connection["access_token"]


# ============== ENDPOINTS ==============

@router.get("/connect")
async def initiate_connection(current_user: dict = Depends(get_current_user)):
    """
    Initiate OAuth2 connection to QuickBooks Online.
    Returns the authorization URL for user to authorize the app.
    """
    if not QB_CLIENT_ID:
        raise HTTPException(status_code=500, detail="QuickBooks credentials not configured")
    
    company_id = current_user.get("company_id")
    user_id = current_user.get("user_id")
    
    # Generate state token for security
    state = secrets.token_urlsafe(32)
    
    # Store state in database for verification
    await db.quickbooks_oauth_states.insert_one({
        "state": state,
        "company_id": company_id,
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10)
    })
    
    # Build authorization URL
    params = {
        "client_id": QB_CLIENT_ID,
        "response_type": "code",
        "scope": "com.intuit.quickbooks.accounting",
        "redirect_uri": QB_REDIRECT_URI,
        "state": state
    }
    
    from urllib.parse import urlencode
    auth_url = f"{QB_AUTHORIZATION_URL}?{urlencode(params)}"
    
    return {
        "authorization_url": auth_url,
        "state": state,
        "message": "Redirect user to authorization_url to connect QuickBooks"
    }


@router.get("/callback")
async def oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    realmId: str = Query(...)
):
    """
    Handle OAuth2 callback from QuickBooks.
    Exchanges authorization code for access tokens.
    """
    try:
        # Verify state parameter
        state_record = await db.quickbooks_oauth_states.find_one({"state": state})
        
        if not state_record:
            raise HTTPException(status_code=400, detail="Invalid or expired state")
        
        # Clean up state record
        await db.quickbooks_oauth_states.delete_one({"state": state})
        
        company_id = state_record["company_id"]
        user_id = state_record["user_id"]
        
        # Exchange authorization code for tokens
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": get_auth_header(),
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            }
            
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": QB_REDIRECT_URI
            }
            
            response = await client.post(
                QB_TOKEN_ENDPOINT,
                headers=headers,
                data=data
            )
            
            if response.status_code != 200:
                raise Exception(f"Token exchange failed: {response.text}")
            
            tokens = response.json()
        
        # Get company info from QuickBooks
        company_name = "QuickBooks Company"
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {tokens['access_token']}",
                    "Accept": "application/json"
                }
                
                # Use sandbox URL for development
                api_url = QB_SANDBOX_API_URL if "sandbox" in QB_REDIRECT_URI.lower() else QB_API_BASE_URL
                response = await client.get(
                    f"{api_url}/{realmId}/companyinfo/{realmId}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    company_info = response.json().get("CompanyInfo", {})
                    company_name = company_info.get("CompanyName", "QuickBooks Company")
        except:
            pass
        
        # Store connection in database
        connection = {
            "company_id": company_id,
            "user_id": user_id,
            "realm_id": realmId,
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "company_name": company_name,
            "expires_at": datetime.now(timezone.utc) + timedelta(seconds=tokens["expires_in"]),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "is_active": True
        }
        
        # Update or insert connection
        await db.quickbooks_connections.update_one(
            {"company_id": company_id},
            {"$set": connection},
            upsert=True
        )
        
        # Get frontend URL from environment
        frontend_url = os.environ.get('FRONTEND_URL', 'https://fortexarh.com')
        
        # Redirect to frontend with success
        return RedirectResponse(
            url=f"{frontend_url}/company-config?tab=integraciones&qb_status=connected&qb_company={company_name}"
        )
        
    except Exception as e:
        frontend_url = os.environ.get('FRONTEND_URL', 'https://fortexarh.com')
        return RedirectResponse(
            url=f"{frontend_url}/company-config?tab=integraciones&qb_status=error&qb_error={str(e)}"
        )


@router.post("/disconnect")
async def disconnect_quickbooks(current_user: dict = Depends(get_current_user)):
    """
    Disconnect QuickBooks integration and revoke tokens.
    """
    company_id = current_user.get("company_id")
    
    # Get connection
    connection = await db.quickbooks_connections.find_one({
        "company_id": company_id,
        "is_active": True
    })
    
    if not connection:
        raise HTTPException(status_code=404, detail="No QuickBooks connection found")
    
    # Revoke token with QuickBooks
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": get_auth_header(),
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            await client.post(
                QB_REVOKE_ENDPOINT,
                headers=headers,
                data={"token": connection["refresh_token"]}
            )
    except:
        pass  # Continue even if revocation fails
    
    # Mark as inactive
    await db.quickbooks_connections.update_one(
        {"company_id": company_id},
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc)}}
    )
    
    return {"status": "success", "message": "QuickBooks disconnected successfully"}


@router.get("/status")
async def get_connection_status(current_user: dict = Depends(get_current_user)):
    """
    Check QuickBooks connection status.
    """
    company_id = current_user.get("company_id")
    
    connection = await db.quickbooks_connections.find_one(
        {"company_id": company_id, "is_active": True},
        {"_id": 0, "access_token": 0, "refresh_token": 0}
    )
    
    if not connection:
        return {
            "connected": False,
            "message": "No QuickBooks connection found"
        }
    
    # Check if token is expired
    expires_at = connection.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    
    is_expired = expires_at < datetime.now(timezone.utc) if expires_at else True
    
    return {
        "connected": True,
        "realm_id": connection.get("realm_id"),
        "company_name": connection.get("company_name"),
        "connected_at": connection.get("created_at"),
        "last_updated": connection.get("updated_at"),
        "token_expired": is_expired
    }


@router.post("/sync/employees")
async def sync_employees_to_quickbooks(current_user: dict = Depends(get_current_user)):
    """
    Sync employees from FortexaRH to QuickBooks as Vendors.
    """
    company_id = current_user.get("company_id")
    user_id = current_user.get("user_id")
    
    # Get valid token
    access_token = await get_valid_token(company_id, user_id)
    if not access_token:
        raise HTTPException(status_code=401, detail="QuickBooks connection expired. Please reconnect.")
    
    # Get connection for realm_id
    connection = await db.quickbooks_connections.find_one({"company_id": company_id, "is_active": True})
    realm_id = connection["realm_id"]
    
    # Get employees
    employees = await db.employees.find(
        {"company_id": company_id, "status": "active"},
        {"_id": 0}
    ).to_list(500)
    
    synced = 0
    errors = []
    
    api_url = QB_SANDBOX_API_URL  # Use sandbox for development
    
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        for emp in employees:
            try:
                # Map employee to QuickBooks Vendor format
                vendor_data = {
                    "DisplayName": f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip(),
                    "GivenName": emp.get("first_name", ""),
                    "FamilyName": emp.get("last_name", ""),
                    "CompanyName": "FortexaRH Employee",
                    "PrimaryEmailAddr": {"Address": emp.get("email")} if emp.get("email") else None,
                    "PrimaryPhone": {"FreeFormNumber": emp.get("phone")} if emp.get("phone") else None,
                }
                
                # Remove None values
                vendor_data = {k: v for k, v in vendor_data.items() if v is not None}
                
                response = await client.post(
                    f"{api_url}/{realm_id}/vendor",
                    headers=headers,
                    json=vendor_data
                )
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    vendor_id = result.get("Vendor", {}).get("Id")
                    
                    # Update employee with QB vendor ID
                    await db.employees.update_one(
                        {"employee_id": emp.get("employee_id"), "company_id": company_id},
                        {"$set": {
                            "qb_vendor_id": vendor_id,
                            "qb_sync_status": "synced",
                            "qb_last_sync": datetime.now(timezone.utc)
                        }}
                    )
                    synced += 1
                else:
                    errors.append({
                        "employee": emp.get("email"),
                        "error": response.text
                    })
            except Exception as e:
                errors.append({
                    "employee": emp.get("email"),
                    "error": str(e)
                })
    
    # Record sync job
    await db.quickbooks_sync_jobs.insert_one({
        "company_id": company_id,
        "user_id": user_id,
        "job_type": "employees",
        "status": "completed",
        "synced_count": synced,
        "error_count": len(errors),
        "errors": errors[:10],  # Store first 10 errors
        "completed_at": datetime.now(timezone.utc)
    })
    
    return {
        "status": "completed",
        "synced": synced,
        "errors": len(errors),
        "error_details": errors[:5] if errors else []
    }


@router.post("/sync/payroll")
async def sync_payroll_to_quickbooks(
    request: SyncRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Sync payroll data to QuickBooks as Journal Entries.
    """
    company_id = current_user.get("company_id")
    user_id = current_user.get("user_id")
    
    # Get valid token
    access_token = await get_valid_token(company_id, user_id)
    if not access_token:
        raise HTTPException(status_code=401, detail="QuickBooks connection expired. Please reconnect.")
    
    # Get connection for realm_id
    connection = await db.quickbooks_connections.find_one({"company_id": company_id, "is_active": True})
    realm_id = connection["realm_id"]
    
    # Get payroll entries
    query = {"company_id": company_id}
    if request.start_date:
        query["created_at"] = {"$gte": request.start_date}
    if request.end_date:
        query["created_at"] = {**query.get("created_at", {}), "$lte": request.end_date}
    
    payroll_entries = await db.payroll_entries.find(query, {"_id": 0}).to_list(500)
    
    synced = 0
    errors = []
    
    api_url = QB_SANDBOX_API_URL  # Use sandbox for development
    
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        for entry in payroll_entries:
            try:
                # Create journal entry for payroll
                journal_entry = {
                    "Line": [
                        {
                            "Description": f"Payroll - {entry.get('employee_name', 'Employee')}",
                            "Amount": float(entry.get("gross_salary", 0)),
                            "DetailType": "JournalEntryLineDetail",
                            "JournalEntryLineDetail": {
                                "PostingType": "Debit",
                                "AccountRef": {"value": "1"}  # Would need actual account mapping
                            }
                        },
                        {
                            "Description": f"Payroll Payable - {entry.get('employee_name', 'Employee')}",
                            "Amount": float(entry.get("gross_salary", 0)),
                            "DetailType": "JournalEntryLineDetail",
                            "JournalEntryLineDetail": {
                                "PostingType": "Credit",
                                "AccountRef": {"value": "2"}  # Would need actual account mapping
                            }
                        }
                    ],
                    "TxnDate": entry.get("payment_date", datetime.now().strftime("%Y-%m-%d"))
                }
                
                response = await client.post(
                    f"{api_url}/{realm_id}/journalentry",
                    headers=headers,
                    json=journal_entry
                )
                
                if response.status_code in [200, 201]:
                    synced += 1
                else:
                    errors.append({
                        "entry": entry.get("entry_id"),
                        "error": response.text
                    })
            except Exception as e:
                errors.append({
                    "entry": entry.get("entry_id"),
                    "error": str(e)
                })
    
    # Record sync job
    await db.quickbooks_sync_jobs.insert_one({
        "company_id": company_id,
        "user_id": user_id,
        "job_type": "payroll",
        "status": "completed",
        "synced_count": synced,
        "error_count": len(errors),
        "completed_at": datetime.now(timezone.utc)
    })
    
    return {
        "status": "completed",
        "synced": synced,
        "errors": len(errors),
        "error_details": errors[:5] if errors else []
    }


@router.get("/sync/history")
async def get_sync_history(
    limit: int = Query(20, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    Get history of QuickBooks sync operations.
    """
    company_id = current_user.get("company_id")
    
    history = await db.quickbooks_sync_jobs.find(
        {"company_id": company_id},
        {"_id": 0}
    ).sort("completed_at", -1).limit(limit).to_list(limit)
    
    return {"history": history}


@router.get("/company-info")
async def get_quickbooks_company_info(current_user: dict = Depends(get_current_user)):
    """
    Get company information from QuickBooks.
    """
    company_id = current_user.get("company_id")
    user_id = current_user.get("user_id")
    
    # Get valid token
    access_token = await get_valid_token(company_id, user_id)
    if not access_token:
        raise HTTPException(status_code=401, detail="QuickBooks connection expired. Please reconnect.")
    
    # Get connection for realm_id
    connection = await db.quickbooks_connections.find_one({"company_id": company_id, "is_active": True})
    realm_id = connection["realm_id"]
    
    api_url = QB_SANDBOX_API_URL  # Use sandbox for development
    
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        response = await client.get(
            f"{api_url}/{realm_id}/companyinfo/{realm_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json().get("CompanyInfo", {})
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)


# ============== WEBHOOKS ==============

import hmac
import hashlib
import logging

logger = logging.getLogger("quickbooks_webhooks")

# Webhook verifier token from Intuit Developer Portal
QB_WEBHOOK_VERIFIER_TOKEN = os.environ.get('QUICKBOOKS_WEBHOOK_VERIFIER_TOKEN', '')


def verify_webhook_signature(payload: bytes, signature: str, verifier_token: str) -> bool:
    """
    Verify the webhook signature from Intuit
    Intuit uses HMAC-SHA256 with the verifier token as the key
    """
    if not verifier_token:
        logger.warning("No webhook verifier token configured")
        return False
    
    try:
        expected_signature = hmac.new(
            verifier_token.encode('utf-8'),
            payload,
            hashlib.sha256
        ).digest()
        
        expected_b64 = base64.b64encode(expected_signature).decode('utf-8')
        return hmac.compare_digest(expected_b64, signature)
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {e}")
        return False


@router.post("/webhook")
async def quickbooks_webhook(request: Request):
    """
    Receive webhook notifications from QuickBooks Online
    
    Intuit sends webhooks for:
    - Account, Bill, BillPayment, Budget, Class, CreditMemo
    - Customer, Employee, Estimate, Invoice, Item, JournalEntry
    - Payment, PaymentMethod, Purchase, PurchaseOrder, Vendor, etc.
    
    Events: Create, Update, Delete, Merge, Void
    """
    try:
        # Get the raw body for signature verification
        body = await request.body()
        
        # Get Intuit signature from headers
        intuit_signature = request.headers.get("intuit-signature", "")
        
        # Verify signature if verifier token is configured
        if QB_WEBHOOK_VERIFIER_TOKEN:
            if not verify_webhook_signature(body, intuit_signature, QB_WEBHOOK_VERIFIER_TOKEN):
                logger.warning("Invalid webhook signature received")
                raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        # Parse the webhook payload
        import json
        try:
            payload = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
        # Log the webhook event
        logger.info(f"QuickBooks webhook received: {json.dumps(payload, indent=2)}")
        
        # Process the webhook events
        event_notifications = payload.get("eventNotifications", [])
        
        processed_events = []
        
        for notification in event_notifications:
            realm_id = notification.get("realmId")
            data_change_event = notification.get("dataChangeEvent", {})
            entities = data_change_event.get("entities", [])
            
            for entity in entities:
                entity_name = entity.get("name")  # e.g., "Account", "Invoice", "Employee"
                entity_id = entity.get("id")
                operation = entity.get("operation")  # Create, Update, Delete, Merge, Void
                last_updated = entity.get("lastUpdated")
                
                # Store webhook event in database
                webhook_event = {
                    "event_id": f"qb_webhook_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
                    "realm_id": realm_id,
                    "entity_name": entity_name,
                    "entity_id": entity_id,
                    "operation": operation,
                    "last_updated": last_updated,
                    "raw_payload": entity,
                    "processed": False,
                    "created_at": datetime.now(timezone.utc)
                }
                
                await db.quickbooks_webhook_events.insert_one(webhook_event)
                
                processed_events.append({
                    "entity": entity_name,
                    "id": entity_id,
                    "operation": operation,
                    "event_id": webhook_event["event_id"]
                })
                
                # Trigger specific handlers based on entity type
                await process_webhook_entity(realm_id, entity_name, entity_id, operation)
        
        logger.info(f"Processed {len(processed_events)} webhook events")
        
        # Intuit expects a 200 OK response
        return {"status": "received", "events_processed": len(processed_events)}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        # Still return 200 to prevent Intuit from retrying
        return {"status": "error", "message": str(e)}


async def process_webhook_entity(realm_id: str, entity_name: str, entity_id: str, operation: str):
    """
    Process specific entity changes from webhooks
    This can trigger automatic syncs or notifications
    """
    try:
        # Find the company connected to this realm
        connection = await db.quickbooks_connections.find_one({
            "realm_id": realm_id,
            "is_active": True
        })
        
        if not connection:
            logger.warning(f"No active connection found for realm {realm_id}")
            return
        
        company_id = connection.get("company_id")
        
        # Create notification for important changes
        important_entities = ["Employee", "Account", "JournalEntry", "Invoice", "Bill", "Payment"]
        
        if entity_name in important_entities:
            # Log to CDC audit system
            from routes.cdc_audit import log_audit_event
            await log_audit_event(
                database=db,
                collection=f"quickbooks_{entity_name.lower()}",
                operation=operation.lower(),
                document_id=entity_id,
                company_id=company_id,
                changes={"source": "quickbooks_webhook", "realm_id": realm_id}
            )
            
            # Create system notification
            notification = {
                "notification_id": f"notif_qb_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
                "company_id": company_id,
                "type": "integration",
                "title": f"QuickBooks: {entity_name} {operation}",
                "message": f"Se ha {'creado' if operation == 'Create' else 'actualizado' if operation == 'Update' else 'eliminado'} un {entity_name} en QuickBooks (ID: {entity_id})",
                "data": {
                    "source": "quickbooks",
                    "entity": entity_name,
                    "entity_id": entity_id,
                    "operation": operation,
                    "realm_id": realm_id
                },
                "is_read": False,
                "created_at": datetime.now(timezone.utc)
            }
            await db.notifications.insert_one(notification)
            
        logger.info(f"Processed {entity_name} {operation} for company {company_id}")
        
    except Exception as e:
        logger.error(f"Error processing webhook entity: {e}")


@router.get("/webhook/events")
async def get_webhook_events(
    limit: int = Query(50, le=200),
    entity_name: Optional[str] = None,
    operation: Optional[str] = None,
    processed: Optional[bool] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get webhook events history"""
    company_id = current_user.get("company_id")
    
    # Get realm_id for this company
    connection = await db.quickbooks_connections.find_one({
        "company_id": company_id,
        "is_active": True
    })
    
    if not connection:
        return {"events": [], "total": 0}
    
    realm_id = connection.get("realm_id")
    
    # Build query
    query = {"realm_id": realm_id}
    
    if entity_name:
        query["entity_name"] = entity_name
    if operation:
        query["operation"] = operation
    if processed is not None:
        query["processed"] = processed
    
    # Fetch events
    events = await db.quickbooks_webhook_events.find(
        query,
        {"_id": 0, "raw_payload": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    total = await db.quickbooks_webhook_events.count_documents(query)
    
    return {
        "events": events,
        "total": total,
        "realm_id": realm_id
    }


@router.post("/webhook/mark-processed/{event_id}")
async def mark_webhook_processed(
    event_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Mark a webhook event as processed"""
    result = await db.quickbooks_webhook_events.update_one(
        {"event_id": event_id},
        {"$set": {"processed": True, "processed_at": datetime.now(timezone.utc)}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return {"message": "Event marked as processed", "event_id": event_id}

