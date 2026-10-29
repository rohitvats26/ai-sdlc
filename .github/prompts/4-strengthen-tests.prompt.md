---
description: Step 4. Review the tests and strengthen them using PIT mutation testing.
mode: agent
---
Goal: find tests that would still pass if a rule were wrong, and fix them. Tests only.

## Before you start (stop and tell me if a check fails)
Steps 2 and 3 are committed and `mvn test` is green. PIT runs: `mvn test-compile org.pitest:pitest-maven:mutationCoverage`. If it cannot run, stop and show me the error.

## Read only these
`src/test/java/**` and the domain classes PIT mutates.

## Skills (open the file if your Copilot does not load it for you)
- `approval-tests` (`.github/skills/approval-tests/SKILL.md`): what to add for each surviving mutant

## Do, in order
1. Table of weak tests: name, what is weak (exception type only, no unchanged-state check, no message check, missing boundary), what to add.
2. Run PIT. Copy `target/pit-reports` to `pit-before` (git ignores it). Write the score as text (killed, survived, percent) in `docs/mutation-testing.md` under "Before".
3. For each surviving mutant add the missing assertion or test. If a mutant is equivalent (cannot change behaviour), say so and skip it; do not chase 100 percent.
4. Run PIT again. Write the score under "After" and list what each new test killed.

## Rules
Change tests only; if you find a production bug, report it and stop. Never delete or loosen a test. Never write a score you did not see in the PIT output.

## Done when
`mvn test` passes and `docs/mutation-testing.md` has both scores as text. Reply: before and after, mutants killed per new test, mutants still alive and why.

## Finish (in this order; details in "Finish protocol" in `.github/copilot-instructions.md`)
1. Log: `python scripts/ai_log.py add --prompt-ref 4-strengthen-tests --action "<one per real thing you did>" --tool-used "<only tools that ran>" --run-tests "mvn -q test" --command-run "mvn test-compile org.pitest:pitest-maven:mutationCoverage"`
2. Commit: `git add -A`, then `git commit -m "test: strengthen approval tests" -m "Why: the mutation run showed tests that would still pass if a rule were wrong"`. Adjust the wording to what you really changed. Skip if only `docs/ai-log/` changed.
3. Tell me the commit hash and message.
