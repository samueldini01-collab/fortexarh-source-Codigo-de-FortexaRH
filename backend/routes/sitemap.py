"""
Dynamic sitemap.xml generator for SEO.
Includes main public routes + all 29 country landing pages (/pais/{slug}).
Served under /api/sitemap.xml to comply with the platform's ingress rules.
"""

import os
from datetime import datetime, timezone
from fastapi import APIRouter, Response

router = APIRouter(tags=["SEO"])

# Slugs must match /app/frontend/src/components/LandingSEO.jsx → COUNTRY_SLUGS
COUNTRY_SLUGS = {
    "DO": "republica-dominicana", "CU": "cuba", "HT": "haiti", "PR": "puerto-rico",
    "CR": "costa-rica", "SV": "el-salvador", "GT": "guatemala", "HN": "honduras",
    "NI": "nicaragua", "PA": "panama", "MX": "mexico", "US": "estados-unidos", "CA": "canada",
    "CO": "colombia", "AR": "argentina", "CL": "chile", "PE": "peru", "EC": "ecuador",
    "VE": "venezuela", "BO": "bolivia", "PY": "paraguay", "UY": "uruguay", "GY": "guyana",
    "SR": "surinam", "BR": "brasil",
    "ES": "espana", "GB": "reino-unido", "FR": "francia", "BE": "belgica",
}

PUBLIC_ROUTES = [
    {"path": "/", "priority": "1.0", "changefreq": "daily"},
    {"path": "/pricing", "priority": "0.9", "changefreq": "weekly"},
    {"path": "/register", "priority": "0.8", "changefreq": "monthly"},
    {"path": "/login", "priority": "0.6", "changefreq": "monthly"},
    {"path": "/soporte", "priority": "0.5", "changefreq": "monthly"},
]

SUPPORTED_LANGS = ["es", "en", "fr", "pt"]


def _public_base_url() -> str:
    # Prefer explicit SEO base; fall back to common prod domain.
    return (
        os.environ.get("SEO_BASE_URL")
        or os.environ.get("PUBLIC_BASE_URL")
        or "https://fortexarh.com"
    ).rstrip("/")


def _xml_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


@router.get("/sitemap.xml", include_in_schema=False)
async def sitemap_xml():
    base = _public_base_url()
    today = datetime.now(timezone.utc).date().isoformat()
    urls = []

    # Core public routes
    for route in PUBLIC_ROUTES:
        loc = f"{base}{route['path']}"
        urls.append(
            f"<url><loc>{_xml_escape(loc)}</loc><lastmod>{today}</lastmod>"
            f"<changefreq>{route['changefreq']}</changefreq>"
            f"<priority>{route['priority']}</priority></url>"
        )

    # Country-specific landing pages + hreflang alternates
    for _code, slug in COUNTRY_SLUGS.items():
        loc = f"{base}/pais/{slug}"
        alternates = "".join(
            f'<xhtml:link rel="alternate" hreflang="{lang}" '
            f'href="{_xml_escape(f"{loc}?lang={lang}")}"/>'
            for lang in SUPPORTED_LANGS
        )
        urls.append(
            f"<url><loc>{_xml_escape(loc)}</loc><lastmod>{today}</lastmod>"
            f"<changefreq>weekly</changefreq><priority>0.8</priority>"
            f"{alternates}</url>"
        )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml">'
        + "".join(urls)
        + "</urlset>"
    )
    return Response(
        content=xml,
        media_type="application/xml",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@router.get("/robots.txt", include_in_schema=False)
async def robots_txt():
    base = _public_base_url()
    body = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /admin\n"
        "Disallow: /super-admin\n"
        "Disallow: /dashboard\n"
        f"Sitemap: {base}/api/sitemap.xml\n"
    )
    return Response(content=body, media_type="text/plain")
