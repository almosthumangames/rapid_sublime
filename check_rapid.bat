@echo off
::http://stackoverflow.com/questions/162291/how-to-check-if-a-process-is-running-via-a-batch-script
 
SET RAPID=C:\Work\projects\rapid\rapid.exe

for /f %%i in ("%0") do set curpath=%%~dpi
cd /d %curpath% 

tasklist /FI "IMAGENAME eq rapid.exe" /FO CSV > search.log
FINDSTR rapid.exe search.log > found.log
FOR /F %%A IN (found.log) DO IF %%~zA EQU 0 GOTO end
   
tasklist /FI "IMAGENAME eq rapid_d.exe" /FO CSV > search.log
FINDSTR rapid_d.exe search.log > found.log
FOR /F %%A IN (found.log) DO IF %%~zA EQU 0 GOTO end

start /DC:\Work\projects\rapid %RAPID%

:end

del search.log
del found.log