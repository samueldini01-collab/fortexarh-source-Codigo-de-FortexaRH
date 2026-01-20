"""
Recruitment Routes - FortexaRH
Handles job postings and candidate management
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import uuid

router = APIRouter(tags=["Recruitment"])

db = None
get_current_user = None


def init_router(database, auth_func):
    global db, get_current_user
    db = database
    get_current_user = auth_func


class JobCreate(BaseModel):
    title: str
    department: str
    location: Optional[str] = None
    type: str = "full-time"
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    description: Optional[str] = None
    requirements: Optional[List[str]] = []
    benefits: Optional[List[str]] = []


class CandidateCreate(BaseModel):
    job_id: str
    name: str
    email: str
    phone: Optional[str] = None
    resume_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    cover_letter: Optional[str] = None
    experience_years: Optional[int] = None


# ===================== JOBS =====================

@router.get("/jobs")
async def get_jobs(current_user: dict = Depends(lambda: get_current_user)):
    jobs = await db.jobs.find(
        {"company_id": current_user.get("company_id")},
        {"_id": 0}
    ).to_list(1000)
    return jobs


@router.post("/jobs")
async def create_job(data: JobCreate, current_user: dict = Depends(lambda: get_current_user)):
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    job = {
        "job_id": job_id,
        "company_id": current_user.get("company_id"),
        **data.model_dump(),
        "status": "open",
        "candidates_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.jobs.insert_one(job)
    return {"job_id": job_id, "message": "Job posting created successfully"}


@router.put("/jobs/{job_id}")
async def update_job(job_id: str, data: JobCreate, current_user: dict = Depends(lambda: get_current_user)):
    result = await db.jobs.update_one(
        {"job_id": job_id, "company_id": current_user.get("company_id")},
        {"$set": data.model_dump()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"message": "Job updated successfully"}


@router.put("/jobs/{job_id}/close")
async def close_job(job_id: str, current_user: dict = Depends(lambda: get_current_user)):
    result = await db.jobs.update_one(
        {"job_id": job_id, "company_id": current_user.get("company_id")},
        {"$set": {"status": "closed", "closed_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"message": "Job closed successfully"}


# ===================== CANDIDATES =====================

@router.get("/candidates")
async def get_candidates(job_id: Optional[str] = None, current_user: dict = Depends(lambda: get_current_user)):
    query = {"company_id": current_user.get("company_id")}
    if job_id:
        query["job_id"] = job_id
    candidates = await db.candidates.find(query, {"_id": 0}).to_list(1000)
    return candidates


@router.post("/candidates")
async def create_candidate(data: CandidateCreate, current_user: dict = Depends(lambda: get_current_user)):
    company_id = current_user.get("company_id")
    
    # Verify job exists
    job = await db.jobs.find_one({"job_id": data.job_id, "company_id": company_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    candidate_id = f"cand_{uuid.uuid4().hex[:12]}"
    candidate = {
        "candidate_id": candidate_id,
        "company_id": company_id,
        **data.model_dump(),
        "job_title": job.get("title"),
        "stage": "new",
        "rating": None,
        "notes": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.candidates.insert_one(candidate)
    
    # Update candidates count
    await db.jobs.update_one(
        {"job_id": data.job_id},
        {"$inc": {"candidates_count": 1}}
    )
    
    return {"candidate_id": candidate_id, "message": "Candidate added successfully"}


@router.put("/candidates/{candidate_id}/stage")
async def update_candidate_stage(candidate_id: str, stage: str, current_user: dict = Depends(lambda: get_current_user)):
    valid_stages = ["new", "screening", "interview", "offer", "hired", "rejected"]
    if stage not in valid_stages:
        raise HTTPException(status_code=400, detail=f"Invalid stage. Must be one of: {', '.join(valid_stages)}")
    
    result = await db.candidates.update_one(
        {"candidate_id": candidate_id, "company_id": current_user.get("company_id")},
        {"$set": {"stage": stage, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return {"message": "Candidate stage updated successfully"}
