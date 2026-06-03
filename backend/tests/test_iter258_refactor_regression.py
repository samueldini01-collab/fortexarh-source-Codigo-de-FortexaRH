"""
Iter 258 — Backend smoke regression after PayrollV2Page + SuperAdminPage refactor.
Refactor was frontend-only; backend behaviour must be identical.

Endpoints under smoke:
  - GET /api/payroll/periods                                          (admin token)
  - GET /api/dgii-reports/native/tss-autodeterminacion-v53?year=2026&month=3
  - GET /api/dgii-reports/native/tss-novedades-v51?year=2026&month=3
  - GET /api/dgii-reports/native/tss-bonificacion-v14?year=2026&month=3
  - GET /api/dgii-reports/native/ir4-official?year=2026&month=3
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "test_refactor@fortexa.com"
ADMIN_PASSWORD = "test123"
OPENXML_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@pytest.fixture(scope="module")
def admin_token():
    assert BASE_URL.startswith("http"), f"REACT_APP_BACKEND_URL invalid: {BASE_URL!r}"
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=30,
    )
    if r.status_code != 200:
        pytest.skip(f"admin login failed: {r.status_code} {r.text[:200]}")
    tok = r.json().get("access_token") or r.json().get("token")
    if not tok:
        pytest.skip(f"no access_token in payload: {list(r.json().keys())}")
    return tok


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# ---------- Payroll ----------
def test_payroll_periods_list(auth_headers):
    r = requests.get(f"{BASE_URL}/api/payroll/periods", headers=auth_headers, timeout=30)
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    # Should be a list (may be wrapped in dict)
    if isinstance(data, dict):
        assert "periods" in data or "items" in data or "data" in data, list(data.keys())
        periods = data.get("periods") or data.get("items") or data.get("data") or []
    else:
        periods = data
    assert isinstance(periods, list)


# ---------- DGII native templates (XLSX) ----------
@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/dgii-reports/native/tss-autodeterminacion-v53",
        "/api/dgii-reports/native/tss-novedades-v51",
        "/api/dgii-reports/native/tss-bonificacion-v14",
        "/api/dgii-reports/native/ir4-official",
    ],
)
def test_dgii_native_template_returns_xlsx(auth_headers, endpoint):
    r = requests.get(
        f"{BASE_URL}{endpoint}",
        params={"year": 2026, "month": 3},
        headers=auth_headers,
        timeout=60,
    )
    assert r.status_code == 200, f"{endpoint} -> {r.status_code} {r.text[:300]}"
    # PK ZIP signature (XLSX is a zip file)
    assert r.content[:2] == b"PK", f"{endpoint} not a zip/xlsx: first bytes {r.content[:8]!r}"
    ct = r.headers.get("content-type", "")
    assert OPENXML_MIME in ct or "octet-stream" in ct or "ms-excel" in ct, ct
    # Reasonable size sanity
    assert len(r.content) > 1500, f"{endpoint} suspiciously small: {len(r.content)} bytes"
