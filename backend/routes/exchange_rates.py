"""Public exchange rates endpoint — landing page uses this to convert USD → local currency."""
from fastapi import APIRouter, Query
from routes.multi_country_reports import _get_fx_rates

router = APIRouter(prefix="/exchange-rates", tags=["exchange-rates"])


@router.get("/latest")
async def latest_rates(base: str = Query("USD", min_length=3, max_length=3)):
    """Return latest FX rates (cached 1h). Public endpoint, no auth required."""
    rates = await _get_fx_rates(base.upper())
    return {
        "base": base.upper(),
        "rates": rates,
        "source": "open.er-api.com",
    }
