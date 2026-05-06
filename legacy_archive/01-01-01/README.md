# Legacy Reference: 01-01-01

This directory is the designated reference location for the `01-01-01` legacy system.

The current repository root may temporarily contain local legacy drops named `01-01`
and `01-01-01`. Those drops are not the maintained system and should not be mixed into
`v2/src/mqre_v2`.

Important direction:

- `v2/src/mqre_v2` remains the formal core.
- `1001plus` is the future strategy research baseline.
- `0313` and `0313plus` are deprecated references only.
- `01-01-01` is not a strategy-core migration source.
- `01-01-01` may only be used for workflow, validation, UX, progress, top10, and
  forward-log concepts.

Rules:

- `01-01-01` is the only legacy reference target.
- `01-01` is deprecated and should not be maintained.
- Legacy content is reference-only.
- Do not overwrite current v2 modules with legacy files.
- Do not migrate 0313 / 0313plus as the formal strategy core.
- Do not copy the old Streamlit / `bundle` / `mq01` architecture into v2.
- Rewrite selected concepts into v2 with tests.

See:

- `docs/legacy/01-01-01_inventory.md`
- `docs/legacy/legacy_to_v2_migration_plan.md`
- `docs/dashboard/html_dashboard_plan.md`
