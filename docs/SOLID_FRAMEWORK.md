# FileCustra SOLID Framework

This project uses SOLID as an engineering discipline for the frontend, sidecar, and Tauri core.

## Single Responsibility

- View components render one product surface or one section of that surface.
- Data loading and normalization live in services such as `runtimeSnapshot.ts`.
- Sidecar functions collect one category of system data at a time: drives, hardware, security, settings, or phase status.
- Filesystem execution stays separate from planning, preview, verification, and rollback.

## Open/Closed

- New dashboard sections should be added as new section components, not by expanding a large render block.
- New runtime snapshot categories should extend `SystemSnapshot` through typed fields and normalization.
- New organization strategies should register as additional strategy objects behind the planner contract.

## Liskov Substitution

- Fallback snapshots and real runtime snapshots must satisfy the same `SystemSnapshot` type.
- Components must work with generated local data or safe fallback data without changing render logic.
- Mock analysis results must follow the same contracts expected from real sidecar output.

## Interface Segregation

- Components receive only the props they need. For example, the dashboard receives `systemSnapshot` and `onOpenWorkspace`, not full app state.
- Services expose focused APIs such as `loadRuntimeSystemSnapshot()`.
- Backend RPC methods stay narrow: `system.snapshot`, `workspace.phase_status`, `magika.classify`, `ocr.extract`, and planner calls do not share loose generic payloads.

## Dependency Inversion

- React views depend on typed snapshot contracts, not on direct OS calls.
- The browser reads generated local JSON; the launcher and sidecar own operating-system inspection.
- Future Tauri commands should depend on domain interfaces for scanning, planning, journaling, and rollback rather than UI-specific structures.

## Current Applied Examples

- `DriveDashboardView.tsx` is split into small section components: dashboard header, command summary, storage web, drive inventory, hardware grid, security/settings, and runtime strip.
- `runtimeSnapshot.ts` maps backend snake_case JSON into frontend camelCase contracts.
- `main.py` generates a local runtime snapshot before Vite starts, keeping machine-specific data outside version control.
- `.gitignore` excludes `frontend/public/system-snapshot.json` because it contains local drive and hardware details.

## Phase Rules

- Every new phase should identify the contract it owns before adding UI.
- Prefer typed data models over ad hoc object shapes.
- Do not let AI planner output call filesystem mutation directly; it must pass through dry-run and journal contracts.
- Keep generated local machine data out of GitHub.
