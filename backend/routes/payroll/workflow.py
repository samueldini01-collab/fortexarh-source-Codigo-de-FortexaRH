"""Workflow — re-export shim after the iter245 split.

Route handlers now live in sibling modules:
- ``approval`` : submit-for-approval, approve, reject
- ``status``   : workflow-status, bank-check, workflow-history

Importing this module keeps the endpoints registered on the shared router.
"""
from . import approval       # noqa: F401
from . import status as _status  # noqa: F401
