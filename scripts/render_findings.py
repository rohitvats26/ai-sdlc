#!/usr/bin/env python3
"""Render docs/review/findings.json as markdown (docs/ai-code-review.md) so the findings are written once."""
import json, sys
items = json.load(open("docs/review/findings.json", encoding="utf-8"))
counts = {v: sum(1 for i in items if i["verdict"] == v) for v in ("fixed", "dismissed", "deferred")}
out = ["# AI code review of the approval-limits change", "",
       "Prompt run (workshop): *Review this PR against our checklist. Report findings by severity with file and line, suggest a fix for each, and say what you are unsure about.*", "",
       "**How this review was done.** A separate pass read `git diff a85def8..HEAD` cold, without the author's reasoning, using the `review-pr` skill checklist, plus two experiments (removing the lock; scanning docs for drift). The reviewer and the author were the same AI model in one chat session, so this is a self-review in two passes, not an independent reviewer. **Verdicts are the author's proposals and must be confirmed by the student, who is accountable for them.**", "",
       f"Result: {len(items)} findings: {counts['fixed']} fixed, {counts['dismissed']} dismissed, {counts['deferred']} deferred. Machine-readable: `docs/review/findings.json` (checked by `scripts/hooks/validate-findings.py --final`).", "",
       "| ID | Severity | Where | Finding | Verdict | Reason / resolution |", "| --- | --- | --- | --- | --- | --- |"]
for i in items:
    reason = i["verdict_reason"] + ((" Resolution: " + i["resolution"]) if i["resolution"] and i["verdict"] == "fixed" else "")
    out.append(f"| {i['id']} | {i['severity']} | `{i['file']}:{i['line']}` | **{i['title']}.** {i['description']} | **{i['verdict'].upper()}** | {reason} |")
out += ["", "## Reviewer uncertainty", ""]
out += [f"- {i['id']}: {i['unsure_about']} (confidence {i['confidence']})" for i in items if i["unsure_about"] != "None."]
open("docs/ai-code-review.md", "w", encoding="utf-8").write("\n".join(out) + "\n")
print("rendered", len(items), "findings")
