#!/usr/bin/env python3
"""Translate missing French (fr.json) keys using Emergent LLM Key (Claude Sonnet 4.5).

Strategy:
1. Compute full set of missing FR keys = (used-in-code missing from fr) ∪ (present in en/es but absent in fr)
2. For each missing key, take source text from en.json (preferred) or es.json (fallback)
3. Translate in batches via emergentintegrations -> Claude Sonnet 4.5
4. Merge translated keys back into fr.json preserving nested structure and key order (merge with existing)
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

FRONTEND_SRC = Path("/app/frontend/src")
LOCALES_DIR = FRONTEND_SRC / "i18n" / "locales"
KEY_PATTERN = re.compile(r"""t\(\s*(['"`])([a-zA-Z0-9_.-]+)\1""", re.MULTILINE)

BATCH_SIZE = 40  # keys per LLM call


def flatten(obj, prefix=""):
    flat = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            nk = f"{prefix}.{k}" if prefix else k
            flat.update(flatten(v, nk))
    else:
        flat[prefix] = obj
    return flat


def unflatten(flat: dict) -> dict:
    """Convert dotted keys back to nested dict."""
    root = {}
    for key, value in flat.items():
        parts = key.split(".")
        node = root
        for p in parts[:-1]:
            if p not in node or not isinstance(node[p], dict):
                node[p] = {}
            node = node[p]
        node[parts[-1]] = value
    return root


def deep_merge(base: dict, updates: dict) -> dict:
    """Merge updates into base (recursive). updates win on leaves; base preserves existing."""
    for k, v in updates.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            deep_merge(base[k], v)
        else:
            # only set if not already present
            if k not in base:
                base[k] = v
    return base


def collect_used_keys():
    used = set()
    for ext in ("*.jsx", "*.js", "*.tsx", "*.ts"):
        for src in FRONTEND_SRC.rglob(ext):
            if "node_modules" in src.parts:
                continue
            try:
                text = src.read_text(errors="ignore")
            except Exception:
                continue
            for match in KEY_PATTERN.finditer(text):
                key = match.group(2)
                if key and "." in key:
                    used.add(key)
    return used


async def translate_batch(batch: list[tuple[str, str]]) -> dict[str, str]:
    """Translate a batch of (key, english_text) tuples to French. Returns {key: french}."""
    from emergentintegrations.llm.chat import LlmChat, UserMessage

    key = os.environ["EMERGENT_LLM_KEY"]
    session_id = f"fr-translation-{os.getpid()}"

    system_prompt = (
        "You are a professional French translator for a SaaS HR & Payroll product named FortexaRH. "
        "Translate short UI strings from English to natural, concise Canadian/European French suitable for a business app. "
        "Rules: (1) Preserve placeholders like {count}, {name}, %s, %d verbatim. "
        "(2) Preserve trailing punctuation. "
        "(3) Keep it short — UI labels. "
        "(4) Do NOT translate product names 'FortexaRH', 'QuickBooks', 'Stripe', 'PayPal'. "
        "(5) Keep CamelCase/acronym terms (e.g., PDF, CSV, XML, DGII, SAT) unchanged. "
        "(6) Output ONLY a JSON object mapping the exact key (dotted) to its French translation. "
        "No prose, no markdown, no code fences."
    )
    payload = {k: v for k, v in batch}
    user_text = (
        "Translate the VALUES of this JSON from English to French. Keep the keys unchanged. "
        "Return only a JSON object with the same keys and French values.\n\n"
        + json.dumps(payload, ensure_ascii=False)
    )

    chat = LlmChat(api_key=key, session_id=session_id, system_message=system_prompt)
    chat.with_model("anthropic", "claude-sonnet-4-5-20250929")
    chat.with_params(max_tokens=4096)

    resp = await chat.send_message(UserMessage(text=user_text))
    # Extract JSON
    text = resp.strip() if isinstance(resp, str) else str(resp)
    # Remove code fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```\s*$", "", text)
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        # Try to find a JSON object substring
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            result = json.loads(match.group(0))
        else:
            print(f"  [WARN] Failed to parse batch response: {text[:200]}")
            return {}
    return {k: (v if isinstance(v, str) else str(v)) for k, v in result.items()}


async def main():
    print("Loading locales...")
    en = json.loads((LOCALES_DIR / "en.json").read_text())
    es = json.loads((LOCALES_DIR / "es.json").read_text())
    fr = json.loads((LOCALES_DIR / "fr.json").read_text())
    en_flat = flatten(en)
    es_flat = flatten(es)
    fr_flat = flatten(fr)

    print(f"  en: {len(en_flat)}  es: {len(es_flat)}  fr: {len(fr_flat)}")

    print("Scanning frontend for used keys...")
    used = collect_used_keys()
    print(f"  used-in-code: {len(used)}")

    # Missing in FR = (keys used in code not in fr) ∪ (keys in en/es not in fr)
    missing = set()
    for k in used:
        if k not in fr_flat:
            missing.add(k)
    for k in en_flat:
        if k not in fr_flat:
            missing.add(k)
    for k in es_flat:
        if k not in fr_flat:
            missing.add(k)

    print(f"  TOTAL missing FR keys: {len(missing)}")

    # Build source material for each
    sources = {}
    for k in missing:
        if k in en_flat and isinstance(en_flat[k], str):
            sources[k] = en_flat[k]
        elif k in es_flat and isinstance(es_flat[k], str):
            # Mark Spanish source so LLM knows
            sources[k] = es_flat[k]
        else:
            # Derive from last segment
            tail = k.split(".")[-1]
            # split camelCase
            derived = re.sub(r"([A-Z])", r" \1", tail).strip().capitalize()
            sources[k] = derived

    # Batch and translate
    items = sorted(sources.items())
    print(f"\nTranslating {len(items)} keys in batches of {BATCH_SIZE}...")

    translations = {}
    batches = [items[i : i + BATCH_SIZE] for i in range(0, len(items), BATCH_SIZE)]
    total = len(batches)
    for idx, batch in enumerate(batches, 1):
        print(f"  Batch {idx}/{total} ({len(batch)} keys)...", end=" ", flush=True)
        try:
            out = await translate_batch(batch)
            translations.update(out)
            print(f"OK ({len(out)})")
        except Exception as e:
            print(f"FAIL: {e}")
            # fallback: keep English/source text
            for k, v in batch:
                if k not in translations:
                    translations[k] = v

    # Fill any missing fallback
    for k, v in sources.items():
        if k not in translations:
            translations[k] = v

    print(f"\nTranslated: {len(translations)}/{len(sources)}")

    # Merge: unflatten translations and deep-merge into fr (preserving existing)
    translated_nested = unflatten(translations)
    merged = deep_merge(fr, translated_nested)

    # Write back
    out_path = LOCALES_DIR / "fr.json"
    out_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n")
    print(f"\nWrote {out_path}")

    # Verify
    new_fr_flat = flatten(merged)
    still_missing = [k for k in sources if k not in new_fr_flat]
    print(f"Still missing after merge: {len(still_missing)}")
    if still_missing[:5]:
        print("  samples:", still_missing[:5])


if __name__ == "__main__":
    asyncio.run(main())
