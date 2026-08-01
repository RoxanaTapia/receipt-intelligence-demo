# /ship-complete Command

You are acting as the **milestone-orchestrator**.

Close the loop after a PR is merged — tick issue acceptance criteria and confirm the issue is done.

## When to use

Run after the human confirms a PR is merged (e.g. "merged" or "PR #NN merged").

## Instructions

1. **Read the issue** — list acceptance criteria checkboxes from the issue body.
2. **Cross-check the merged PR** — confirm each criterion was verified (agent in `/verify`, human in PR test plan).
3. **Tick issue checkboxes** — use `gh issue edit` to mark all met criteria as checked in the issue body.
4. **Confirm issue state** — if the PR used `Closes #NN`, the issue should already be closed; report status.

## Rules

- Do **not** tick criteria that were not verified in the PR.
- Do **not** re-open or merge PRs — this is housekeeping only.
- If a criterion was not met, report it instead of ticking.

## Output format

```markdown
## Ship-complete summary

**Issue:** #NN
**PR:** #NN (merged)

### Acceptance criteria

| Criterion | Verified by | Issue checkbox |
|-----------|-------------|--------------|
| ... | Agent / Human (PR #NN) | ✅ ticked |

**Issue state:** closed / open
```
