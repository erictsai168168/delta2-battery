# delta2-battery

**English** | [繁體中文](README.zh-TW.md)

A tiny, dark and flat Windows tray app that shows the battery level of an **ASUS ROG Delta II** headset connected through its **2.4 GHz dongle** — no Armoury Crate required. Built with Claude Sonnet 5.5. Yes, even on the free plan.

> **Unofficial project.** This is an independent, community-made tool. It is not affiliated with, endorsed by, or supported by ASUSTeK Computer Inc. "ASUS" and "ROG" are trademarks of ASUSTeK Computer Inc., used here only to describe which hardware the tool works with.

<!-- TODO: add a screenshot of the main window and the tray icon here -->

## Features

- Reads the battery level straight from the 2.4 GHz receiver over USB HID, and refreshes it automatically (every 30 s).
- Small, flat, dark window you can drag around; lives in the system tray when closed.
- Tray icon shows the number: green, amber (≤ 30 %) and red (≤ 15 %).
- While charging, a lightning bolt appears next to the number in the window, and the tray number slowly "breathes" (fades in and out).
- Low-battery notification at 20 % (re-armed once the level is back to 30 % or more).
- Optional start with Windows, starting minimized to the tray.
- Single instance, no installer, no background service.

## Download

Grab the latest build from the [Releases](../../releases) page:

| File | What it is |
| --- | --- |
| `DeltaBattery.exe` | Single-file build. Easiest, but more likely to be flagged by antivirus (see below). |
| `DeltaBattery-folder.zip` | Folder build. Unzip and run `DeltaBattery.exe` — keep the whole folder together. |

Windows 64-bit, no Python needed. Built and tested on the author's machine only.

## Usage

1. Plug in the headset's 2.4 GHz receiver and turn the headset on.
2. Start the app. The battery level appears within a few seconds.
3. Right-click the tray icon for **Show window**, **Refresh now**, **Start with Windows**, **Quit**.

Status text in the window:

| Status | Meaning |
| --- | --- |
| 2.4G connected | Receiver found and the headset is answering. |
| Headset not connected | Receiver found, but the headset is off or out of range. |
| Receiver not detected | No supported receiver is plugged in. |

If you use Armoury Crate, close it first if the app cannot read the receiver — both may try to talk to the same device.

## Supported hardware

| Item | Value |
| --- | --- |
| Headset | ASUS ROG Delta II (2.4 GHz mode) |
| Receiver USB ID | `VID 0x0B05` / `PID 0x1AFA` |

Developed and tested on a single unit (black edition). **Other editions (e.g. the white one), regions or firmware versions may use a different PID or different data.** If yours does not work, please open a *Hardware report* issue and attach the output of the tools in [`tools/`](tools/) — that is the fastest way to add support.

## Run from source

```bat
pip install hidapi PySide6
python delta2_battery.py
```

Python 3.9+ on Windows. Add `--minimized` to start in the tray only.

## Build the exe

```bat
build.bat            :: folder build  -> dist\DeltaBattery\DeltaBattery.exe
build_onefile.bat    :: single file   -> dist\DeltaBattery.exe
```

Pushing a tag like `v0.1.0` also builds both with GitHub Actions and attaches them to a release.

## How it works

The receiver exposes a vendor-defined HID interface (usage page `0xFF00`). The app writes a 64-byte query and reads the 64-byte answer; the headset also pushes updates by itself when it connects or when the charger is plugged in or out. The details, including how they were found, are in [`docs/PROTOCOL.md`](docs/PROTOCOL.md).

The app only **reads status**. It never writes settings to the headset, never touches firmware, and does not use any ASUS code.

## Antivirus warnings

Executables made with PyInstaller are sometimes flagged by Microsoft Defender and other antivirus software as a **false positive**, especially the single-file build. The source code in this repository is everything the app does. If your antivirus complains, you can:

- use the folder build instead of the single-file one,
- run it from source with Python (see above), or
- build it yourself with `build.bat`.

## Known limitations

- Windows only.
- Only tested with one headset/receiver; the charging flag value (`1` = charging) is verified on that unit only. It can be flipped with `CHARGING_VALUE` in `delta2_core.py`.
- Bluetooth and wired modes are not supported: the app only talks to the 2.4 GHz receiver.
- This is reverse-engineered from observed USB traffic, so a firmware update may change the behavior.

## Contributing & maintenance

This is a hobby project made in spare time, not a full-time effort — replies and fixes may be slow, and there is no guarantee of support. **Pull requests are very welcome**, especially new PIDs, firmware reports and bug fixes. When reporting a problem, please include your Windows version, the receiver's VID/PID and the output of the tools in `tools/`.

## License

[MIT](LICENSE). Provided as is, without warranty of any kind.
