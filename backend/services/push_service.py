"""
Push Notification Service - FortexaRH
Sends web push notifications via VAPID protocol.
"""
import os
import json
import logging
from pywebpush import webpush, WebPushException
from config import db

logger = logging.getLogger(__name__)

VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY")
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY")
VAPID_CLAIMS_EMAIL = os.environ.get("VAPID_CLAIMS_EMAIL", "mailto:noreply@fortexaerp.com")


async def send_push_to_user(user_id: str, title: str, body: str, url: str = "/", data: dict = None):
    """Send push notification to all subscriptions of a user."""
    if not VAPID_PUBLIC_KEY or not VAPID_PRIVATE_KEY:
        logger.warning("VAPID keys not configured, skipping push notification")
        return 0

    subscriptions = await db.push_subscriptions.find(
        {"user_id": user_id}, {"_id": 0}
    ).to_list(50)

    if not subscriptions:
        return 0

    payload = json.dumps({
        "title": title,
        "body": body,
        "url": url,
        **({"data": data} if data else {})
    })

    sent = 0
    expired_endpoints = []

    for sub in subscriptions:
        subscription_info = {
            "endpoint": sub["endpoint"],
            "keys": sub.get("keys", {})
        }
        try:
            webpush(
                subscription_info=subscription_info,
                data=payload,
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims={"sub": VAPID_CLAIMS_EMAIL}
            )
            sent += 1
        except WebPushException as e:
            if e.response and e.response.status_code in (404, 410):
                expired_endpoints.append(sub["endpoint"])
            logger.error(f"Push failed for user {user_id}: {e}")
        except Exception as e:
            logger.error(f"Push error for user {user_id}: {e}")

    if expired_endpoints:
        await db.push_subscriptions.delete_many({
            "user_id": user_id,
            "endpoint": {"$in": expired_endpoints}
        })

    return sent


async def send_push_to_role(company_id: str, role: str, title: str, body: str, url: str = "/"):
    """Send push notification to all users with a given role in a company."""
    users = await db.users.find(
        {"company_id": company_id, "role": role},
        {"_id": 0, "user_id": 1}
    ).to_list(500)

    total = 0
    for user in users:
        total += await send_push_to_user(user["user_id"], title, body, url)
    return total
