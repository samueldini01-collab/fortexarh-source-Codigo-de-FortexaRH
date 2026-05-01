"""Payroll core — kept as a re-export hub after the iter243 split.

The actual route handlers now live in sibling modules:
- ``periods``         : GET/POST/GET-by-id/DELETE /periods + add-employees
- ``entries``         : GET/PUT/DELETE /entries/{id}
- ``novelties``       : POST/DELETE /entries/{id}/novelties
- ``payment``         : /periods/{id}/calculate + /periods/{id}/pay
- ``workflow``        : submit-for-approval, approve, reject, workflow-status,
                        bank-check, workflow-history
- ``journal_entries`` : toggle-auto-je, generate-je, delete-je

This shim exists for any legacy code that did ``from routes.payroll.core
import ...``. Importing it ensures sub-modules are loaded so endpoints register.
"""
from . import periods         # noqa: F401
from . import entries         # noqa: F401
from . import novelties       # noqa: F401
from . import payment         # noqa: F401
from . import workflow        # noqa: F401
from . import journal_entries  # noqa: F401
