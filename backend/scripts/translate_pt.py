#!/usr/bin/env python3
"""Generate pt.json (Brazilian Portuguese) translations from es.json baseline.

Strategy:
1. Start from es.json as the most culturally-close source (Spanish -> Portuguese is easier
   than English -> Portuguese for Latin-America business terminology, fiscal vocabulary, etc.)
2. Translate every leaf value via Emergent LLM Key (Claude Sonnet 4.5) in batches of 40 keys.
3. Preserve placeholders like {count}, {{name}}, %s, product names (FortexaRH, QuickBooks, DGII).
4. Output /app/frontend/src/i18n/locales/pt.json AND /app/frontend/public/locales/pt.json.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

SRC_LOCALES_DIR = Path("/app/frontend/src/i18n/locales")
PUBLIC_LOCALES_DIR = Path("/app/frontend/public/locales")
BATCH_SIZE = 40


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


async def translate_batch(batch: list[tuple[str, str]]) -> dict[str, str]:
    from emergentintegrations.llm.chat import LlmChat, UserMessage

    key = os.environ["EMERGENT_LLM_KEY"]
    chat = LlmChat(
        api_key=key,
        session_id=f"pt-translation-{os.getpid()}",
        system_message=(
            "You are a professional Brazilian Portuguese translator for a SaaS HR & Payroll product named FortexaRH. "
            "Translate short UI strings from Spanish to natural, concise Brazilian Portuguese (pt-BR) suitable for a business app. "
            "Rules: "
            "(1) Preserve placeholders like {count}, {{name}}, %s, %d verbatim. "
            "(2) Preserve trailing punctuation and capitalization style. "
            "(3) Keep UI labels SHORT. "
            "(4) Do NOT translate product names 'FortexaRH', 'QuickBooks', 'Stripe', 'PayPal', 'Resend'. "
            "(5) Keep acronyms unchanged: PDF, CSV, XML, DGII, TSS, AFP, SFS, ISR (for DR context). "
            "    For Brazil-specific fiscal: use INSS, IRRF, FGTS naturally when Spanish uses generic SS/pensión/cesantía. "
            "(6) Use Brazilian conventions: 'E-mail' (not 'Correo'), 'Senha' (not 'Contraseña'), 'Cadastro' (not 'Registro' when referring to sign-up). "
            "(7) Output ONLY a JSON object mapping the exact key (dotted) to its Portuguese translation. "
            "No prose, no markdown, no code fences."
        ),
    )
    chat.with_model("anthropic", "claude-sonnet-4-5-20250929")
    chat.with_params(max_tokens=4096)

    payload = {k: v for k, v in batch}
    user_text = (
        "Translate the VALUES of this JSON from Spanish to Brazilian Portuguese (pt-BR). "
        "Keep the keys unchanged. Return only a JSON object with the same keys and Portuguese values.\n\n"
        + json.dumps(payload, ensure_ascii=False)
    )

    resp = await chat.send_message(UserMessage(text=user_text))
    text = resp.strip() if isinstance(resp, str) else str(resp)
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```\s*$", "", text)
    try:
        return {k: (v if isinstance(v, str) else str(v)) for k, v in json.loads(text).items()}
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return {k: (v if isinstance(v, str) else str(v)) for k, v in json.loads(match.group(0)).items()}
            except json.JSONDecodeError:
                pass
        print(f"  [WARN] Failed to parse: {text[:200]}")
        return {}


async def main():
    print("Loading es.json as base...")
    es = json.loads((SRC_LOCALES_DIR / "es.json").read_text())
    es_flat = flatten(es)
    print(f"  es.json: {len(es_flat)} leaf keys")

    # Check existing pt.json - if already present, only translate missing
    pt_path = SRC_LOCALES_DIR / "pt.json"
    pt_existing = {}
    if pt_path.exists():
        try:
            pt_existing = flatten(json.loads(pt_path.read_text()))
            print(f"  existing pt.json: {len(pt_existing)} keys (will only translate missing)")
        except Exception:
            pt_existing = {}

    # Build translate list: all es keys NOT already in pt
    to_translate = {k: v for k, v in es_flat.items() if k not in pt_existing and isinstance(v, str)}
    print(f"  keys to translate: {len(to_translate)}")

    if not to_translate:
        print("Nothing to translate. Exiting.")
        return

    items = sorted(to_translate.items())
    batches = [items[i : i + BATCH_SIZE] for i in range(0, len(items), BATCH_SIZE)]
    total = len(batches)

    translations = dict(pt_existing)  # start with existing
    print(f"\nTranslating {len(items)} keys in {total} batches of {BATCH_SIZE}...")
    for idx, batch in enumerate(batches, 1):
        print(f"  Batch {idx}/{total} ({len(batch)} keys)...", end=" ", flush=True)
        try:
            out = await translate_batch(batch)
            translations.update(out)
            print(f"OK ({len(out)})")
        except Exception as e:
            print(f"FAIL: {e}")
            # Fallback: keep Spanish source
            for k, v in batch:
                if k not in translations:
                    translations[k] = v

    # Ensure all keys are filled (fallback to Spanish source)
    for k, v in es_flat.items():
        if k not in translations and isinstance(v, str):
            translations[k] = v

    # Unflatten and write
    nested = unflatten(translations)
    pt_path.write_text(json.dumps(nested, ensure_ascii=False, indent=2) + "\n")
    print(f"\nWrote {pt_path}  ({len(translations)} keys)")

    # Sync to public/locales
    public_path = PUBLIC_LOCALES_DIR / "pt.json"
    public_path.write_text(json.dumps(nested, ensure_ascii=False, indent=2) + "\n")
    print(f"Wrote {public_path}")

    # Verify
    final = flatten(nested)
    missing = [k for k in es_flat if k not in final]
    print(f"\nFinal pt.json keys: {len(final)}  missing vs es: {len(missing)}")


if __name__ == "__main__":
    asyncio.run(main())
