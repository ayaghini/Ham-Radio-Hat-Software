# APRS Comms Tab (`CommsTab`)

`v4` uses a merged APRS + messaging tab. There is no separate standalone APRS tab in the notebook.

## Left Panel

### APRS Source

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Callsign | Entry | `aprs_source_var` | Sets source callsign used for APRS TX and chat routing. | Set your station callsign-SSID. |

### RX Monitor

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Start | Button | `start_rx_monitor()` | Starts continuous APRS RX decode loop. | Begin live monitoring. |
| Stop | Button | `stop_rx_monitor()` | Stops monitor thread and cleanup flow. | End monitoring. |
| One-Shot | Button | `rx_one_shot()` | Runs one-shot capture/decode. | Spot-check receive path quickly. |
| Monitor indicator | Label | `set_monitor_active()` | Shows `MONITORING` marker while RX monitor is active. | Visual monitor-state indicator. |
| Level | Label | `aprs_rx_level_var` via `set_input_level()` | Shows live input level percent. | Track receive signal level. |
| Clip | Label | `rx_clip_var` via `set_rx_clip()` | Shows clip percent, warns when elevated. | Detect overdriven RX audio. |
| Auto-ACK | Checkbutton | `aprs_auto_ack_var` | Enables automatic ACK for direct APRS messages addressed to local station. | Reliable-message interoperability. |
| Always-on | Checkbutton | `aprs_rx_auto_var`, `on_rx_auto_toggle()` | Auto-start/stop monitor from checkbox state. | Keep passive monitoring enabled. |

### Contacts / Groups / Heard

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Contacts list | Listbox | `refresh_contacts()` from `CommsManager.contacts` | Displays direct contacts, adds unread marker when needed. | Click contact to open active thread. |
| Add... | Button | `_add_contact()` -> `add_contact()` | Prompts callsign and stores contact. | Add direct message peers. |
| Remove | Button | `_remove_contact()` -> `remove_contact()` | Removes selected contact after confirmation. | Clean up contact list. |
| <- Heard | Button | `_import_heard_to_contacts()` | Imports heard stations into contacts. | Build contacts from live traffic. |
| Groups list | Listbox | `refresh_contacts()` from `CommsManager.groups` | Displays groups with member count and unread marker. | Click group to open active group thread. |
| New... | Button | `_new_group()` -> `set_group()` | Creates group from name + CSV members. | Define broadcast groups. |
| Edit... | Button | `_edit_group()` -> `set_group()` | Edits selected group members. | Maintain group membership. |
| Delete | Button | `_delete_group()` -> `delete_group()` | Deletes selected group. | Remove unused groups. |
| Group members text | Label | `_group_members_var` | Shows members of selected group. | Validate selected group definition. |
| Heard Stations list | Listbox | `refresh_heard()` from `CommsManager.heard` | Shows heard calls with unread marker when relevant. | Open a thread with recently heard stations. |
| Clear Heard | Button | `_clear_heard()` -> `clear_heard()` | Clears heard list. | Reset heard history. |

### Intro / Position TX

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Note | Entry | `_intro_note_var` | Text used in `@INTRO` packet payload. | Set short discovery message. |
| Lat | Entry | `aprs_lat_var` | Used for intro/position payload coordinates. | Set station latitude. |
| Lon | Entry | `aprs_lon_var` | Used for intro/position payload coordinates. | Set station longitude. |
| Comment | Entry | `aprs_comment_var` | Position comment text. | Add beacon/status note. |
| Send Intro | Button | `_send_intro()` -> `send_intro()` | Sends intro discovery packet using current source/lat/lon/note. | Announce station presence. |
| Send Position | Button | `_send_position()` -> `send_aprs_position()` | Sends APRS position packet. | Beacon your position. |

## Right Panel

### Stations Map

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Stations map canvas | `TiledMapCanvas` | `add_map_point()` and map callbacks | Shows APRS station points on offline/online tile-backed map. | Visual station tracking. |
| Clear | Button | `_clear_map()` | Clears plotted map points. | Reset map view/history. |
| Open in Browser | Button | `_open_map_in_browser()` | Opens last plotted location in OpenStreetMap. | External map detail view. |
| Download Tiles... | Button | `DownloadRegionDialog` | Opens tile-download dialog for offline caching by bounds/zoom. | Prepare offline map coverage. |

### Messages

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Active thread label | Label | `_thread_label` | Displays currently active contact/group thread. | Confirms current message target context. |
| Message log | `BoundedLog` | `_load_thread()`, `_render_message()`, `on_message()` | Shows thread history with TX/RX/system formatting and delivered markers. | Read conversation history. |
| Compose box | Multi-line `Text` | `_compose_text`; Enter handler | Enter sends, Shift+Enter inserts newline. | Write outgoing messages. |
| Reliable | Checkbutton | `_reliable_var` | Enables reliable send mode for direct messages. Ignored for group sends. | Require ACK/retry on direct messages. |
| Send | Button | `_send_message()` | Sends to currently active thread (contact or selected group). | Main chat send action. |

## APRS Log

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| APRS Log panel | `BoundedLog` | `append_log()` via APRS events | Logs APRS TX/RX/reliable/map/system lines. | APRS diagnostics and activity trace. |

## Behavioral Notes

| Component | Actual behavior |
|---|---|
| Send targeting | Send actions target `CommsManager.active_thread`; there is no standalone `To:` field in this tab. |
| Thread activation | Selecting a contact/heard station/group opens that thread and updates unread markers. |
| Group send behavior | Group thread sends call `send_group_message()` and ignore the `Reliable` checkbox. |
| Tile download | `DownloadRegionDialog` estimates tile count, supports cancel, and writes to tile cache used by map canvas. |
