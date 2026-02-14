"""MongoDB utility helpers for FortexaRH"""
from bson import ObjectId


def sanitize_doc(doc):
    """Remove _id from a MongoDB document and convert ObjectIds to strings"""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [sanitize_doc(d) for d in doc]
    if isinstance(doc, dict):
        return {
            k: str(v) if isinstance(v, ObjectId) else sanitize_doc(v)
            for k, v in doc.items()
            if k != "_id"
        }
    return doc
