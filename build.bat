@echo off
rem 打包成資料夾模式：產出在 dist\DeltaBattery\DeltaBattery.exe
rem 資料夾模式不會在執行時解壓縮到暫存區，被防毒誤判的機率比單檔模式低很多。
rem 發佈或搬移時請整個 dist\DeltaBattery 資料夾一起帶走。
pip install -r requirements.txt
rmdir /s /q build dist 2>nul
pyinstaller --noconsole --onedir --noupx --clean --name DeltaBattery delta2_battery.py
echo.
echo 完成：dist\DeltaBattery\DeltaBattery.exe
pause
