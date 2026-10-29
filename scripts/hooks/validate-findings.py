#!/usr/bin/env python3
"""Validate the review findings file: fixed keys, allowed values, a verdict on every finding.

Usage: validate-findings.py [--if-exists] [--final] FILE
  --final   additionally require every verdict to be fixed/dismissed/deferred with a reason (no 'pending').
Exit 2 on failure so a hook feeds the message back to the agent.
"""
import json, os, sys

KEYS = ["id", "severity", "file", "line", "title", "description", "suggested_fix",
        "confidence", "unsure_about", "verdict", "verdict_reason", "resolution"]
SEVERITY = {"critical", "high", "medium", "low", "info"}
CONFIDENCE = {"high", "medium", "low"}
VERDICT = {"fixed", "dismissed", "deferred", "pending"}


def validate(items, final):
    errors = []
    if not isinstance(items, list) or not items:
        return ["file must be a non-empty JSON array"]
    seen = set()
    for index, item in enumerate(items):
        where = f"finding #{index + 1}"
        if not isinstance(item, dict):
            errors.append(f"{where}: not an object"); continue
        if list(item.keys()) != KEYS and set(item.keys()) != set(KEYS):
            errors.append(f"{where}: keys must be exactly {KEYS}")
            continue
        if item["id"] in seen: errors.append(f"{where}: duplicate id {item['id']}")
        seen.add(item["id"])
        if item["severity"] not in SEVERITY: errors.append(f"{where}: bad severity")
        if item["confidence"] not in CONFIDENCE: errors.append(f"{where}: bad confidence")
        if item["verdict"] not in VERDICT: errors.append(f"{where}: bad verdict")
        if final:
            if item["verdict"] == "pending": errors.append(f"{where}: verdict still pending")
            if not str(item["verdict_reason"]).strip(): errors.append(f"{where}: verdict_reason required")
            if item["verdict"] == "fixed" and not str(item["resolution"]).strip():
                errors.append(f"{where}: fixed needs a resolution")
    return errors


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        print("usage: validate-findings.py [--if-exists] [--final] FILE", file=sys.stderr); return 2
    path = args[0]
    if not os.path.exists(path):
        if "--if-exists" in argv: return 0
        print(f"{path} not found", file=sys.stderr); return 2
    try:
        with open(path, encoding="utf-8") as handle:
            items = json.load(handle)
    except Exception as exc:
        print(f"{path}: invalid JSON: {exc}", file=sys.stderr); return 2
    errors = validate(items, "--final" in argv)
    for error in errors: print(error, file=sys.stderr)
    if not errors: print(f"{path}: {len(items)} findings valid")
    return 2 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
