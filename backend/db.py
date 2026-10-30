import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("JOB_MATCHING_DB_NAME", "job_matching_capstone")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Collections
candidats_col = db["candidats"]
offres_col = db["offres"]
decisions_col = db["decisions"]
audit_trail_col = db["audit_trail"]
dlq_col = db["decisions_dlq"]


def log_audit(event_type: str, payload: dict):
    """Jour 18 : enregistre chaque decision/action importante dans audit_trail."""
    entry = {
        "event_type": event_type,
        "payload": payload,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    audit_trail_col.insert_one(entry)
    return entry


def log_dlq(reason: str, payload: dict):
    """Jour 22 : enregistre les cas en echec dans la Dead Letter Queue."""
    entry = {
        "reason": reason,
        "payload": payload,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    dlq_col.insert_one(entry)
    return entry