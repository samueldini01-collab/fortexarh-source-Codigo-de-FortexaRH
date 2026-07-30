import asyncio
import os
import sys

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")
STATUS = sys.argv[1]
COMPANY = "comp_7bf9f34ab85e"


async def main():
    c = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = c[os.environ["DB_NAME"]]
    await db.subscriptions.update_one({"company_id": COMPANY}, {"$set": {"status": STATUS}}, upsert=True)
    sub = await db.subscriptions.find_one({"company_id": COMPANY}, {"_id": 0, "status": 1})
    print("status now:", sub)
    c.close()


asyncio.run(main())
