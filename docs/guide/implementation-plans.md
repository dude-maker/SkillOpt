# Central Implementation Plans

SkillOpt can validate the structured HTML plans maintained in the separate
`implementation-plans` repository. The plan repository is the writable source
of truth for cross-repository implementation state; SkillOpt does not silently
modify it.

## Validate and resume

```bash
python -m skillopt_sleep plan-validate \
  --plan-path "$IMPLEMENTATION_PLANS_ROOT/plans/comfyui-newsroom-automation.html"
```

Use JSON output for scripts:

```bash
python -m skillopt_sleep plan-validate \
  --plan-path "$IMPLEMENTATION_PLANS_ROOT/plans/comfyui-newsroom-automation.html" --json
```

The validator checks section status, test commands, acceptance criteria,
completion evidence, dependencies, and final sign-off. It also reports the
first actionable section so an interrupted implementation can resume without
guessing.

Lifecycle timestamps use `America/New_York` and include the explicit ISO-8601
offset. Every update appends a change-history entry; section start, completion,
blockage, and plan updates are therefore auditable.

Plan updates remain reviewable artifacts in the master repository. SkillOpt's
existing staging and adoption gates apply when SkillOpt proposes changes to a
planning skill or plan content.
