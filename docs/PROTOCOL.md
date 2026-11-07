# Protocol notes (ROG Delta II, 2.4 GHz receiver)

Reverse-engineered by observing USB HID traffic on **one** unit. Nothing here comes from ASUS documentation or code. It may be incomplete or wrong for other editions or firmware versions — please report differences.

## Device

| Item | Value |
| --- | --- |
| USB VID / PID | `0x0B05` / `0x1AFA` (product string `ROG DELTA II (2.4GHz)`) |
| Interface | `MI_03`, exposed by Windows as four HID collections |

The four HID collections on `MI_03`:

| Collection | Usage page / usage | Use |
| --- | --- | --- |
| `Col01` | `0x000C` / `0x0001` (Consumer) | Volume up/down keys: reports `0C 01` (up), `0C 02` (down), `0C 00` (release). Not related to battery. |
| `Col02` | `0xFF13` / `0x0001` | Vendor page. Nothing was observed on it. |
| `Col03` | `0x000B` / `0x0005` (Telephony) | Nothing was observed on it. |
| `Col04` | `0xFF00` / `0x0001` | **Vendor page — status and battery (used by this app).** |

The app selects the interface by **usage page `0xFF00`**, not by interface number or device path, so it works regardless of the USB port or machine.

## Report format (usage page `0xFF00`)

All reports are 64 bytes. Byte 0 is `0xCC`, byte 1 is `0x12`, byte 2 selects the field:

```
CC 12 <field> 00 00 <value> 00 00 ... (zero padded to 64 bytes)
 0  1    2     3  4    5
```

| Field (byte 2) | Meaning | Byte 5 | Confidence |
| --- | --- | --- | --- |
| `0x09` | **Battery level** | Percentage, `0x00`–`0x64` (e.g. `0x30` = 48 %, `0x36` = 54 %) | Confirmed: the value tracked the actual level, and rose while charging. |
| `0x08` | **Charging state** | `0` / `1`. It toggled every time the charger was plugged in or out. `1` is assumed to mean "charging" (see below). | Field confirmed by plugging/unplugging; polarity inferred, see below. |
| `0x00` | Unknown | Byte 4 was `01`, byte 5 was `00` or `01`. Appeared when the headset connected. | Unknown meaning (possibly link state). |

### Polarity of the charging field

While probing, the field ended in state `1` and the battery level was seen *rising* (48 % → 54 % in a few minutes), so `1` is treated as "charging". This was observed on one unit only. It is a single constant, `CHARGING_VALUE` in `delta2_core.py`, if it turns out to be reversed on yours.

## Talking to the receiver

- **Query:** write 64 bytes `CC 12 <field> 00 ...` to the `0xFF00` collection. The receiver answers with a report of the same layout carrying the value. Both a 64-byte and a 65-byte write (with a leading report-ID byte) were accepted and answered with the same 64-byte report.
- **Push:** the headset also sends the `0x00`, `0x08` and `0x09` reports by itself when it connects, and `0x08` when the charger is plugged in or out.
- **Feature reports:** reading and sending feature reports does not work on this collection.
- **Connection state:** there is no explicit "headset is off" report that was identified. The app treats "no answer to a query within a few seconds" as *headset not connected*.

The app only sends the two read-style queries for fields `0x09` and `0x08` (all other bytes zero). It never sends anything intended to change a setting.

## How to reproduce / report on your hardware

1. Close Armoury Crate and any ASUS background services.
2. Run `python tools/probe_delta2.py --listen 40`, and during the 40 s turn the headset off and on, press the volume buttons, and plug/unplug the charger.
3. Run `python tools/probe_delta2_query.py` and note the battery level the official app shows at that moment.
4. Open a *Hardware report* issue and paste the contents of `probe_result.txt` and `probe_query_result.txt`, together with your receiver's VID/PID (Device Manager → Properties → Details → Hardware Ids).
