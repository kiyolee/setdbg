setlocal

set PYVER=36
set PYW32=-32

set PY=C:\Python%PYVER%%PYW32%\python.exe
set FREEZE=C:\Python%PYVER%%PYW32%\scripts\cxfreeze.py

set EXCLUDE_MODS=
set INCLUDE_MODS=

set EXCLUDE_MODS=pyreadline,readline,pdb,opcode,select,optparse,pickle,StringIO,unittest,inspect,headq,calendar,doctest,tempfile,random,bz2
rem set INCLUDE_MODS=encodings.ascii
set INCLUDE_MODS=

if defined EXCLUDE_MODS set EXCLUDE_OPTS=--exclude-modules=%EXCLUDE_MODS%
if defined INCLUDE_MODS set INCLUDE_OPTS=--include-modules=%INCLUDE_MODS%

set APP_NAME=setdbg
set DIST_DIR=%APP_NAME%.cxdist.%PYVER%

%PY% %FREEZE% --target-dir=%DIST_DIR% %EXCLUDE_OPTS% %INCLUDE_OPTS% ..\%APP_NAME%.py

endlocal
