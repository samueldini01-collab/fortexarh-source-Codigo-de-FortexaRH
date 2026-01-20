"""
Evaluations Routes - FortexaRH
Handles performance evaluations
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/evaluations", tags=["Evaluations"])

db = None
get_current_user = None


def init_router(database, auth_func):
    global db, get_current_user
    db = database
    get_current_user = auth_func


class EvaluationCreate(BaseModel):
    employee_id: str
    title: str
    period: str
    type: str = "performance"
    criteria: Optional[List[Dict[str, Any]]] = []
    comments: Optional[str] = None


@router.get("")
async def get_evaluations(current_user: dict = Depends(lambda: get_current_user)):
    evaluations = await db.evaluations.find(
        {"company_id": current_user.get("company_id")},
        {"_id": 0}
    ).to_list(1000)
    return evaluations


@router.post("")
async def create_evaluation(data: EvaluationCreate, current_user: dict = Depends(lambda: get_current_user)):
    company_id = current_user.get("company_id")
    
    employee = await db.employees.find_one(
        {"employee_id": data.employee_id, "company_id": company_id},
        {"_id": 0}
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Calculate overall score from criteria
    total_score = 0
    if data.criteria:
        scores = [c.get("score", 0) for c in data.criteria if c.get("score")]
        total_score = sum(scores) / len(scores) if scores else 0
    
    evaluation_id = f"eval_{uuid.uuid4().hex[:12]}"
    evaluation = {
        "evaluation_id": evaluation_id,
        "company_id": company_id,
        "employee_id": data.employee_id,
        "employee_name": f"{employee['first_name']} {employee['last_name']}",
        "department": employee.get("department"),
        "position": employee.get("position"),
        "title": data.title,
        "period": data.period,
        "type": data.type,
        "criteria": data.criteria or [],
        "overall_score": round(total_score, 2),
        "comments": data.comments,
        "status": "draft",
        "evaluator_id": current_user["user_id"],
        "evaluator_name": current_user.get("name"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.evaluations.insert_one(evaluation)
    
    return {"evaluation_id": evaluation_id, "message": "Evaluation created successfully"}
