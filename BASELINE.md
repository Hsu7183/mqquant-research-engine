# Core Baseline

The historical `01-01-01` workbench was the original mqquant research baseline.

In the v2 standard repository, the old `01-01-01/` bundle is no longer stored as a live project folder. It was removed because it was a legacy data/workbench package and is no longer imported or executed by the maintained system.

Current baseline governance is represented by:

- WFO specifications in `docs/WFO_SPEC.md`
- baseline-vs-challenger decision logic in `mqre_v2.validation.decision`
- dashboard reports in `runs/latest/reports/`
- strategy registry records
- decision audit logs

Rules:

1. Do not restore or edit the historical `01-01-01` workbench in the standard repo.
2. All strategy changes must be evaluated through the current v2 pipeline.
3. All results must be compared against the selected baseline report.
4. All forward tests must record baseline vs challenger context.

The baseline is now a governed report/registry concept, not a live legacy folder.
