# Run Reports

One detailed report per work session ("run"), written **immediately after the run finishes** and
committed with (or right after) the run's work. Purpose: the user builds the next step's prompt
from the newest report alone — every number, path, command and open decision it needs must be
here, so nothing is re-derived from memory or re-measured from disk.

## Naming

```
RUN-<YYYY-MM-DD>-<nn>_<slug>.md
```

* `nn` = 01, 02, … in date order (multiple runs per day allowed).
* `slug` = short kebab-case description of what the run did
  (e.g. `phase4-completion`, `phase5-fold-training`).

## Template (copy into every new report)

```markdown
# Run Report RUN-<date>-<nn> — <title>

**Date:** <date> · **Session goal:** <one line>
**Starting state:** <baseline commit / where the previous run left off>
**End state:** <commit hash, tree clean yes/no, suite status>

## 1. What was run, in order
| # | Command / file | Purpose | Result (exit, key numbers) |

## 2. Measured values (do not re-derive)
<the numbers this run produced or confirmed, each traceable to its file>

## 3. Bugs caught and fixes
<every failure met during the run, what it was, and the fix applied>

## 4. Verification and gates
<suites run, pass/fail counts, anything not green>

## 5. Outputs produced or changed
<files written/modified, what each contains, where they live>

## 6. Current project state
<phase status, what exists and what explicitly does not (model/metrics/maps)>

## 7. Next-step handoff (prompt material)
- **Decisions the user must make:** <questions needing user input>
- **What the next step must do / must not do:** <constraints carried forward>
- **Quick commands:** <verify / re-run / inspect>
- **Do not re-derive:** <measured facts that must be quoted as-is>
```

## Rules

* Written at the end of **every** run — no exceptions, even for short runs.
* Every number in section 2 must come from a file on disk (a JSON/CSV output), never from
  memory; cite the file.
* Section 7 is the payload: it should be possible to draft the next prompt from it verbatim.
* The report is a record, not a plan: it states what happened, and flags decisions, it does not
  decide them.
