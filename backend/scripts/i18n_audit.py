#!/usr/bin/env python3
"""i18n audit — detect missing translation keys per locale.

Scans every .jsx/.js file under /app/frontend/src for patterns:
- t('key.path')
- t("key.path")
- t('key', 'fallback')
- t(`key.path`)   — conservatively reported

Compares the union of keys used in code against the flattened keys present
in each locale JSON file (/app/frontend/src/i18n/locales/*.json).

Output per locale: list of missing keys.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

FRONTEND_SRC = Path("/app/frontend/src")
LOCALES_DIR = FRONTEND_SRC / "i18n" / "locales"

# Match t('...'), t("..."), t(`...`) — the first positional argument.
# We accept any number of trailing arguments after a comma.
KEY_PATTERN = re.compile(
    r"""t\(\s*(['"`])([a-zA-Z0-9_.-]+)\1""",
    re.MULTILINE,
)


def _flatten(obj, prefix: str = "") -> dict[str, str]:
    """Flatten nested JSON into dotted keys."""
    flat = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{prefix}.{k}" if prefix else k
            flat.update(_flatten(v, new_key))
    else:
        flat[prefix] = obj
    return flat


def _load_locales() -> dict[str, set[str]]:
    """Return {locale: set_of_flat_keys}."""
    locales = {}
    for p in sorted(LOCALES_DIR.glob("*.json")):
        locale = p.stem
        try:
            data = json.loads(p.read_text())
            locales[locale] = set(_flatten(data).keys())
            print(f"  Loaded {locale}: {len(locales[locale])} keys")
        except Exception as exc:  # noqa: BLE001
            print(f"  FAILED to load {p}: {exc}")
    return locales


def _collect_used_keys() -> dict[str, list[Path]]:
    """Return {used_key: [files_using_it]}."""
    used = defaultdict(list)
    for ext in ("*.jsx", "*.js", "*.tsx", "*.ts"):
        for src in FRONTEND_SRC.rglob(ext):
            if "node_modules" in src.parts:
                continue
            try:
                text = src.read_text(errors="ignore")
            except Exception:  # noqa: BLE001
                continue
            for match in KEY_PATTERN.finditer(text):
                key = match.group(2)
                if key and "." in key:  # require namespaced keys
                    used[key].append(src.relative_to(FRONTEND_SRC))
    return dict(used)


def main():
    print("Loading locales...")
    locales = _load_locales()

    print("\nScanning frontend sources...")
    used_keys = _collect_used_keys()
    print(f"  Found {len(used_keys)} distinct translation keys in use.")

    missing_report: dict[str, list[tuple[str, list[Path]]]] = {loc: [] for loc in locales}
    for key, files in sorted(used_keys.items()):
        for loc, loc_keys in locales.items():
            if key not in loc_keys:
                missing_report[loc].append((key, files))

    print("\n" + "=" * 70)
    print("i18n AUDIT REPORT")
    print("=" * 70)
    for loc, missing in missing_report.items():
        print(f"\n🌐 Locale: {loc}")
        print(f"   Missing keys: {len(missing)}")
        if missing:
            for key, files in missing[:40]:  # cap output
                files_str = ", ".join(str(f) for f in files[:2])
                more = f" +{len(files) - 2}" if len(files) > 2 else ""
                print(f"     ❌ {key}  ({files_str}{more})")
            if len(missing) > 40:
                print(f"     ... and {len(missing) - 40} more")

    # Report common keys present in ONE locale but not others (inconsistency)
    print("\n" + "=" * 70)
    print("INCONSISTENT KEYS (present in some locales but not others)")
    print("=" * 70)
    all_keys = set().union(*(s for s in locales.values()))
    inconsistent = []
    for k in sorted(all_keys):
        locales_with = [loc for loc, keys in locales.items() if k in keys]
        if len(locales_with) != len(locales):
            missing_from = [loc for loc in locales if loc not in locales_with]
            inconsistent.append((k, missing_from))
    print(f"  Total inconsistent keys: {len(inconsistent)}")
    for k, missing_from in inconsistent[:25]:
        print(f"     ⚠️  {k}  — missing from: {', '.join(missing_from)}")
    if len(inconsistent) > 25:
        print(f"     ... and {len(inconsistent) - 25} more")

    # Write JSON report
    report_path = Path("/tmp/i18n_audit_report.json")
    report_path.write_text(json.dumps({
        "summary": {
            "total_keys_used_in_code": len(used_keys),
            "locales": {loc: {
                "total_keys": len(keys),
                "missing_from_code": len(missing_report[loc]),
            } for loc, keys in locales.items()},
            "inconsistent_keys_count": len(inconsistent),
        },
        "missing_per_locale": {
            loc: [{"key": k, "files": [str(f) for f in files]} for k, files in missing]
            for loc, missing in missing_report.items()
        },
        "inconsistent_keys": [
            {"key": k, "missing_from": mf} for k, mf in inconsistent
        ],
    }, indent=2, ensure_ascii=False))
    print(f"\n📄 Full JSON report saved to: {report_path}")


if __name__ == "__main__":
    main()
