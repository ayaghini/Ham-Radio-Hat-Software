# APRS Tab (`AprsTab`) - Legacy Note

There is no standalone APRS notebook tab in `ham_hat_control_center_v4`.

APRS controls were merged into:
- `APRS Comms` tab for RX monitor, map, contacts/groups, intro/position TX, messaging, and APRS logs.
- `Setup` tab for APRS TX/RX advanced tuning fields (destination/path/gain/preamble/retries/ACK/RX trim/OS level).

Use these docs instead:
- `comms-tab.md`
- `setup-tab.md`

Historical context:
- Earlier versions had a separate `AprsTab` widget; current app wiring in `app/app.py` instantiates only `MainTab`, `CommsTab`, and `SetupTab`.
