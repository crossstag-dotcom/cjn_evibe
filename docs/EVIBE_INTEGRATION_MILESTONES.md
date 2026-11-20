# EVIBE & DENVIX — integration milestones and scope guard

This document tracks the ongoing work so new requests do not displace unfinished milestones. Work on `develop/evibe-platform-redesign`; do not change `main` without approval.

## Non-negotiable rules
- Audit before adding. Reuse existing dashboards, product catalog, manufacturing services, login, and mobile prototypes. Do not rebuild completed work.
- Do not redesign dashboard layouts unless requested.
- Do not modify the existing login behavior until the owner reviews proposed changes.
- Do not finalize wholesale development until the owner reviews requested wholesale changes.
- Distinguish code committed, CI-tested, integrated, and deployed; none are interchangeable.
- Factory departments (cutting/stitching/QC) are not separate finished-goods warehouses.

## Track A: original manufacturing and web backend (continues)
1. Fabric receipt/DC validation, verified roll posting and raw-material stock movement.
2. Cutting roll issue, completion, leftovers and size-wise output.
3. Stitching dispatch, receipt, discrepancies and reconciliation.
4. Washing/processing, QC, finishing, SKU-linked finished goods and one physical FG warehouse.
5. Actual material consumption, production costing, permissions, reconciliation and end-to-end testing.
6. Preserve existing dashboard and wire real backend summaries into its current components.
7. Generate/review/commit Django migrations; run CI and resolve failures before declaring tests passed.

## Track B: shared mobile backend (parallel)
- Reuse Django models and services; authenticated JSON endpoints must enforce per-user permissions.
- Current implemented read-only routes:
  - `GET /api/manufacturing/summary/` (schema_version 1)
  - `GET /api/manufacturing/cutting-completions/<id>/reconciliation/`
- Existing endpoints rely on Django staff sessions and permissions; **native authentication is NOT implemented**.
- Next: confirm mobile UI contracts, consistent JSON 401/403 semantics after login review, pagination and stable versioned API namespace before release.
- Never expose staff manufacturing data to customer-only sessions.

## Track C: native iOS and Android (parallel)
- Preserve existing responsive mobile/PWA designs and locate their source before recreating screens.
- Native project sources and builds are **not yet verified in this repository**.
- Evaluate shared cross-platform shell (e.g. React Native) only after locating earlier React/Lovable work and reviewing integration constraints.
- Native login, secure credential storage, push notifications, device testing and app-store builds are **not yet implemented or verified**.

## Authentication review gate — owner input required
The repository currently contains two distinct identity paths:
1. Django staff/admin accounts and permission checks.
2. Customer engagement email-OTP/customer-lead sessions (`evibe_customer_id`), separate from Django staff auth.

Customer OTP endpoints currently use `csrf_exempt`. Do not reuse these endpoints as a native staff authentication mechanism without a security review. Record the owner's requested login changes before editing existing auth flows.

## Wholesale review gate — owner input required
Owner has changes to discuss. Stop before wholesale module implementation and review requirements.

## Verified versus pending
- Existing manufacturing services, read-only dashboard summary and read-only JSON API: committed on development branch.
- Manufacturing regression tests: written; successful CI execution not yet verified.
- Migrations for newly added manufacturing models: pending generation/review/commit.
- Existing dashboard visual wiring: pending.
- Native iOS/Android app source/builds: not verified.
- Deployment: not verified.

## Next execution sequence
1. Resolve migrations and obtain actual CI results.
2. Connect the existing dashboard template/components to the committed read-only summary.
3. Locate earlier mobile UI source; map screens to shared backend APIs.
4. Review owner-requested login changes before native sign-in integration.
5. Continue factory workflow beyond stitching, with tests at each stage.
