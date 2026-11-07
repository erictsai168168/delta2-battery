@echo off
rem 打包成「單一 exe」：產出 dist\DeltaBattery.exe，只要這一個檔案就能獨立執行。
rem 注意：單檔模式被防毒誤判的機率比資料夾模式（build.bat）高。
pip install -r requirements.txt
rmdir /s /q build dist 2>nul
pyinstaller --noconsole --onefile --noupx --clean --name DeltaBattery delta2_battery.py
rem 清掉打包過程的暫存，只留 dist\DeltaBattery.exe
rmdir /s /q build 2>nul
del /q DeltaBattery.spec 2>nul
echo.
echo 完成：dist\DeltaBattery.exe（可單獨複製到任何地方使用）
pause
