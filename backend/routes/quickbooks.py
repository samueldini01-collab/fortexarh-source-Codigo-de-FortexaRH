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
security = HTTPBearer(auto_error=False)

db = None
_get_current_user_func: Callable = None

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


def init_router(database, auth_dependency: Callable):
    global db, _get_current_user_func
    db = database
    _get_current_user_func = auth_dependency


async def get_current_user(request: Request, credentials=Depends(security)):
    if _get_current_user_func is None:
        raise HTTPException(status_code=500, detail="Auth not initialized")
    return await _get_current_user_func(request, credentials)


# ============== MODELS ==============

class QuickBooksConnection(BaseModel):
    user_id: str
    company_id: str
    access_token: str
    refresh_token: str
    realm_id: str
    company_name: Optional[str] = None
    expires_at: datetime
    created_at: datetime
    updated_at: datetime
    is_active: bool = True


class SyncRequest(BaseModel):
    sync_type: str  # employees, payroll, vendors, all
    start_date: Optional[str] = None
    end_date: Optional[str] = None


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
