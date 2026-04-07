Work in `/Users/macmini4/Desktop/Ham-Radio-Hat-Software`.

Primary target:
- `/Users/macmini4/Desktop/Ham-Radio-Hat-Software/app`

Planning workspace:
- `/Users/macmini4/Desktop/Ham-Radio-Hat-Software/cross-platform-v4`

Read only these first:
1. `/Users/macmini4/Desktop/Ham-Radio-Hat-Software/README.md`
2. `/Users/macmini4/Desktop/Ham-Radio-Hat-Software/cross-platform-v4/roadmap.md`
3. `/Users/macmini4/Desktop/Ham-Radio-Hat-Software/cross-platform-v4/task-board.md`
4. `/Users/macmini4/Desktop/Ham-Radio-Hat-Software/cross-platform-v4/validation-plan.md`
5. `/Users/macmini4/Desktop/Ham-Radio-Hat-Software/cross-platform-v4/support-matrix.md`
6. `/Users/macmini4/Desktop/Ham-Radio-Hat-Software/app/audit_v4.md`

Current repo truth:
- `app/` is the only active app
- `archive/` contains historical snapshots
- macOS source-run validation is largely complete and SA818 TX/PTT/audio workflow is confirmed
- macOS packaged-app validation is substantially complete; remaining checks need Accessibility permission or BLE hardware
- Raspberry Pi source-run bring-up is confirmed, but item-by-item validation still remains
- Linux desktop validation is still pending
- Linux packaging build has not yet been run
- main remaining work is Raspberry Pi validation, Linux validation, packaging verification, and hardware-backed PAKT validation

Default expectations:
- prefer small direct fixes over broad rewrites
- keep docs current if you materially change status
- do not treat archived packages as active implementation targets
- do not claim platform support you did not verify

Baseline verification:
- `python3 -m compileall -q -x '\\.venv' /Users/macmini4/Desktop/Ham-Radio-Hat-Software/app`
- `python3 /Users/macmini4/Desktop/Ham-Radio-Hat-Software/app/main.py --help`
- `python3 /Users/macmini4/Desktop/Ham-Radio-Hat-Software/app/scripts/platform_validation.py`
- any focused checks related to your task

Expected output:
- concise status summary
- findings and fixes
- updated docs if status changed
- verification results
