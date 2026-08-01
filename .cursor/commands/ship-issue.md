# /ship-issue Command

You are acting as the **milestone-orchestrator**.

Ship a GitHub issue using `AGENTS.md`, `milestone-orchestrator.md` (shipping pipeline), and `.cursor/rules/elegant-minimal-python.mdc`.

## Instructions

1. **Read the issue** and classify acceptance criteria: agent / human / shared.
2. **Plan specialists** — see specialist table in `milestone-orchestrator.md` (`deploy-engineer`, `demo-ux-engineer`, docs/verifier gates).
3. **Human checkpoints** — pause using the template in `milestone-orchestrator.md` when required.
4. Create branch: `feat/<short-description>`.
5. **Implement** — granular commits; only the orchestrator commits.
6. **`/document`** — run docs-writer review only if docs-writer triggers in `milestone-orchestrator.md` match; apply edits, commit. Otherwise note "docs-writer skipped — no doc deliverables" in the PR.
7. **`/verify`** — always before PR; maps every acceptance criterion (block if any ❌ missing).
8. **Open PR** — title without issue numbers; Main contribution paragraph; `Closes #NN` in the body; test plan copied from issue acceptance criteria; human approval before push or merge.
9. **After merge** — human runs or requests **`/ship-complete #NN`** to tick issue checkboxes.

## Output Expectations

- State each step clearly; propose commit messages before committing.
- Ask for confirmation before creating the PR.
- Use human checkpoint or blocker templates when needed.

## Goal

Ship reliably with clean git history and complete documentation handoff.
