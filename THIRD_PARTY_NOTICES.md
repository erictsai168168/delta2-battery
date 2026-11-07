# Third-party notices / 第三方授權聲明

This project's own source code is released under the [MIT License](LICENSE).
The pre-built executables (`DeltaBattery.exe` and `DeltaBattery-folder.zip`) additionally bundle the third-party software listed below, which remains under its own license.

本專案自身的原始碼以 [MIT 授權](LICENSE) 釋出。預先打包好的執行檔（`DeltaBattery.exe` 與 `DeltaBattery-folder.zip`）另外包含下列第三方軟體，這些軟體仍然適用各自的授權。

> This is an informational summary, not legal advice. License terms can change between versions; the authoritative text is the license shipped with each package you install (see "Where to find the full license texts").
> 以下為資訊性整理，並非法律意見。授權條款可能隨版本改變，請以各套件隨附的授權全文為準（見「授權全文在哪裡」）。

## Summary / 總覽

| Component | Used for | License | Bundled in the exe |
| --- | --- | --- | --- |
| [PySide6](https://doc.qt.io/qtforpython-6/) (Qt for Python) and the Qt libraries | Window, tray icon, drawing | LGPL-3.0 (also offered under GPL-3.0 and a commercial license) | Yes |
| [hidapi](https://github.com/trezor/cython-hidapi) (Python binding) and [HIDAPI](https://github.com/libusb/hidapi) | Reading the USB HID receiver | BSD-style license (also offered under GPL-3.0 and the original HIDAPI license) | Yes |
| [Python](https://www.python.org/) runtime | Runs the app | PSF License | Yes |
| [PyInstaller](https://pyinstaller.org/) | Builds the exe | GPL-2.0-or-later **with a special exception** that allows the bundled app to be distributed under any license | Its bootloader is the exe's launcher |

No fonts, images or icons from third parties are bundled. The UI uses the Segoe UI font if it is installed on the user's Windows system.

沒有包含任何第三方字型、圖片或圖示。介面使用使用者 Windows 系統上已安裝的 Segoe UI 字型。

## Qt / PySide6 (LGPL-3.0)

The app uses PySide6 and Qt **unmodified**, as downloaded from PyPI, and links to them dynamically. In accordance with the LGPL-3.0:

- Qt and PySide6 remain the property of their respective owners and are licensed under the GNU Lesser General Public License v3.0: <https://www.gnu.org/licenses/lgpl-3.0.html>
- The corresponding source code of PySide6 and Qt is available from the Qt Project: <https://code.qt.io/> and <https://www.qt.io/download-open-source>
- You are free to replace the Qt / PySide6 libraries with your own build. The **folder build** (`DeltaBattery-folder.zip`) keeps the libraries as separate files so they can be swapped; alternatively, run the app from source (`pip install hidapi PySide6` and `python delta2_battery.py`) against any compatible PySide6 version.
- This license does not restrict your rights to modify this app's own code (MIT).

The Qt libraries in turn contain further third-party components with their own licenses; see <https://doc.qt.io/qt-6/licenses-used-in-qt.html>.

本程式**未修改**地使用從 PyPI 取得的 PySide6 與 Qt，並以動態連結方式使用，依 LGPL-3.0 規定：Qt 與 PySide6 歸其各自所有人所有；其對應原始碼可從 Qt Project 取得（上方連結）；你可以自行替換 Qt / PySide6 函式庫，資料夾版保留了獨立檔案方便替換，也可以直接用原始碼搭配任何相容版本的 PySide6 執行。

## HIDAPI / hidapi (BSD-style)

The Python binding `hidapi` and the underlying HIDAPI library are available under a choice of the GNU GPL v3, a BSD-style license, or the original HIDAPI license. This project uses and redistributes them under the **BSD-style** terms, which require that the copyright notice, the list of conditions and the disclaimer are retained. The notice is reproduced in the package's own license file; see the links below.

`hidapi` 與底層的 HIDAPI 可選擇以 GNU GPL v3、BSD 風格授權或原始 HIDAPI 授權使用。本專案依 **BSD 風格**條款使用與散布，條件是保留版權聲明、條件清單與免責聲明，內容見該套件的授權檔（連結如下）。

## Python (PSF License)

The executables include the CPython runtime, licensed under the Python Software Foundation License: <https://docs.python.org/3/license.html>

## PyInstaller (GPL-2.0-or-later with exception)

The executables are created with PyInstaller. PyInstaller is licensed under GPL-2.0-or-later with a special exception that explicitly allows the programs it builds to be distributed under any license, so this does not change this project's MIT license. See <https://pyinstaller.org/en/stable/license.html>.

## Where to find the full license texts / 授權全文在哪裡

- **When installed with pip:** each package's license file is in `site-packages/<package>-<version>.dist-info/` (usually under `licenses/` or as `LICENSE*`).
- **Online:**
  - PySide6 / Qt: <https://www.qt.io/qt-licensing>
  - hidapi (Python): <https://github.com/trezor/cython-hidapi>
  - HIDAPI: <https://github.com/libusb/hidapi>
  - Python: <https://docs.python.org/3/license.html>
  - PyInstaller: <https://pyinstaller.org/en/stable/license.html>

## Trademarks / 商標

"ASUS" and "ROG" are trademarks of ASUSTeK Computer Inc. "Qt" is a trademark of The Qt Company Ltd. All other names are the property of their respective owners. This project is not affiliated with or endorsed by any of them.

「ASUS」「ROG」為華碩電腦股份有限公司（ASUSTeK Computer Inc.）之商標，「Qt」為 The Qt Company Ltd. 之商標，其他名稱屬於各自所有人。本專案與上述公司皆無關聯，亦未獲其背書。
