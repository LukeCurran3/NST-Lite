@echo off
:: NST nightly sync -- runs on msassneocandod1 via Windows Task Scheduler.
:: Trigger: daily at 3:00 AM, run as Luke's CWRU domain account.
:: Log rotates daily so a single file does not grow unbounded.

set LOG=C:\nst\logs\sync_%date:~-4%%date:~4,2%%date:~7,2%.log

echo === NST sync %date% %time% === >> %LOG%
cd /d C:\nst\app
C:\nst\venv\Scripts\python.exe scripts\nst_sync.py >> %LOG% 2>&1
echo === done %time% === >> %LOG%
