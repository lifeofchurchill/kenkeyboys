@echo off
rem Imports EA match results into the LIVE database.
rem .env points at the dev copy; .env.live holds the live DATABASE_URL.

rem Work from the folder this file is in (the project folder)
cd /d "%~dp0"

rem Stop if .env.live is missing, so results never land in the dev copy by mistake
if not exist ".env.live" (
    echo .env.live is missing - import skipped.
    pause
    exit /b 1
)

rem Load each NAME=value line from .env.live (lines starting with # are skipped).
rem Django's .env loader never overwrites a value already set, so live wins.
for /f "usebackq eol=# tokens=1,* delims==" %%A in (".env.live") do set "%%A=%%B"

rem Run the import and show the result in this window
echo Importing EA results into the LIVE database...
venv\Scripts\python.exe -X utf8 manage.py import_ea_matches

rem Keep the window open so you can read the result
pause