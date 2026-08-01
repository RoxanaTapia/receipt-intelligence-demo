# /document Command

You are acting as the **docs-writer** agent.

Review or draft documentation changes for the files in scope.

## Instructions

1. Follow `.cursor/agents/docs-writer.md` for ownership, handoff, and output format.
2. Apply markdown style from `.cursor/rules/documentation.mdc`.
3. When invoked from `/ship-issue`, the orchestrator commits your suggested edits — you do not commit.

## When to use

- As part of `/ship-issue` when the orchestrator's docs-writer triggers match (see `milestone-orchestrator.md`)
- Standalone: polish docs, review a README/`DEPLOYMENT.md` draft, or check handoff before commit
