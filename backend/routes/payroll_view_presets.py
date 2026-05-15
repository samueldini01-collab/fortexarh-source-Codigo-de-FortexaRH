"""
Payroll view presets.

Lets each user save multiple named column-layout configurations for the
Payroll Sheet (`/payroll`) and re-apply them with one click. Presets are
scoped to the user, so different roles inside a company can keep their
own "Vista Contabilidad", "Vista Auditoría", etc.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from config import db
from utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payroll/view-presets", tags=["Payroll View Presets"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _sanitize(doc: dict) -> dict:
    if not doc:
        return doc
    doc.pop("_id", None)
    for k in ("created_at", "updated_at"):
        v = doc.get(k)
        if isinstance(v, datetime):
            doc[k] = v.isoformat()
    return doc


class PresetIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    order: list[str]
    visible: dict[str, bool]
    is_default: bool = False


class PresetUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=80)
    order: Optional[list[str]] = None
    visible: Optional[dict[str, bool]] = None
    is_default: Optional[bool] = None


def _user_scope(user: dict) -> dict:
    return {
        "user_id": user.get("user_id") or user.get("id") or user.get("email"),
        "company_id": user.get("company_id"),
    }


@router.get("")
async def list_presets(user: dict = Depends(get_current_user)):
    scope = _user_scope(user)
    cursor = db.payroll_view_presets.find(
        scope, {"_id": 0}
    ).sort([("is_default", -1), ("name", 1)])
    docs = await cursor.to_list(length=100)
    return [_sanitize(d) for d in docs]


@router.post("", status_code=201)
async def create_preset(payload: PresetIn, user: dict = Depends(get_current_user)):
    scope = _user_scope(user)
    # Avoid duplicate name per user.
    if await db.payroll_view_presets.find_one({**scope, "name": payload.name}):
        raise HTTPException(status_code=409, detail="Ya existe un preset con ese nombre")

    if payload.is_default:
        await db.payroll_view_presets.update_many(scope, {"$set": {"is_default": False}})

    doc = {
        **scope,
        "preset_id": f"pvp_{uuid.uuid4().hex[:16]}",
        "name": payload.name.strip(),
        "order": payload.order,
        "visible": payload.visible,
        "is_default": payload.is_default,
        "created_at": _now(),
        "updated_at": _now(),
    }
    await db.payroll_view_presets.insert_one(doc)
    return _sanitize({**doc})


@router.patch("/{preset_id}")
async def update_preset(preset_id: str, payload: PresetUpdate, user: dict = Depends(get_current_user)):
    scope = _user_scope(user)
    existing = await db.payroll_view_presets.find_one({**scope, "preset_id": preset_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Preset no encontrado")

    update = {k: v for k, v in payload.model_dump(exclude_none=True).items() if v is not None}
    if not update:
        return _sanitize({**existing})

    if "name" in update:
        clash = await db.payroll_view_presets.find_one({
            **scope, "name": update["name"], "preset_id": {"$ne": preset_id},
        })
        if clash:
            raise HTTPException(status_code=409, detail="Ya existe un preset con ese nombre")
        update["name"] = update["name"].strip()

    if update.get("is_default"):
        await db.payroll_view_presets.update_many(
            {**scope, "preset_id": {"$ne": preset_id}},
            {"$set": {"is_default": False}},
        )

    update["updated_at"] = _now()
    await db.payroll_view_presets.update_one(
        {**scope, "preset_id": preset_id}, {"$set": update}
    )
    updated = await db.payroll_view_presets.find_one(
        {**scope, "preset_id": preset_id}, {"_id": 0}
    )
    return _sanitize(updated)


@router.delete("/{preset_id}")
async def delete_preset(preset_id: str, user: dict = Depends(get_current_user)):
    scope = _user_scope(user)
    result = await db.payroll_view_presets.delete_one({**scope, "preset_id": preset_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Preset no encontrado")
    return {"deleted": True}


async def create_payroll_view_preset_indexes():
    try:
        await db.payroll_view_presets.create_index(
            [("user_id", 1), ("company_id", 1), ("preset_id", 1)], unique=True
        )
        await db.payroll_view_presets.create_index(
            [("user_id", 1), ("company_id", 1), ("name", 1)], unique=True
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"payroll_view_presets index warning: {exc}")
