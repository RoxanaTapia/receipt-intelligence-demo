# /verify Command

You are acting as the **verifier** agent.

Review the current changes and map them against the issue acceptance criteria before a PR opens.

## Instructions

1. **Read the issue** — list every acceptance criterion.
2. Review code and doc changes against `.cursor/rules/elegant-minimal-python.mdc` and `.cursor/rules/documentation.mdc`.
3. Run relevant checks if possible (Compose config, linting, tests, link resolution).
4. **Map each criterion** — ✅ agent-verified, ⏳ human (PR test plan), or ❌ missing (see `verifier.md`).
5. Provide feedback using the verification format below.

## Output format

```markdown
## Verification Summary

- **Status**: ✅ Pass / ⚠️ Issues found / ❌ Needs work
- **Checks performed**:

### Acceptance criteria coverage

| Criterion | Verdict | Evidence |
|-----------|---------|----------|
| ... | ✅ Agent / ⏳ Human / ❌ Missing | ... |

- **Issues found**:
  - ...
- **Suggestions**:
  - ...
```

**Pass rule:** no ❌ criteria. ⏳ criteria must appear in the PR test plan.
