# setdbg

This is a handy utility to set automatic start-up debugger.

For Windows, registry setting "Image File Execution Options" is a well
known method to start some debugger automatically whenever certiain
named executable is executed.  Manually changing the setting using
regedit can be tidious though, especially so if needed to locate the
debugger first.

This utility locates all known debuggers from Microsoft and let you
enable/disable a set of executables that starts with the debugger of
your choice.

*Note*: Need administrative privileges to use.

### Usage examples:

```
C:\> setdbg -h

usage 1: setdbg.py [options] [-e|--enable {exe} ...] [-d|--disable {exe} ...]
    Enable/disable starting debugger for an executable upon execution.

options:
    --msvc6, --vc6
        Use MSVC6 as debugger if available
    --vs(2003|2005|2008|2010|2012|2013|2015|2017)
        Use Visual Studio as debugger if available
    --windbg, --windbg_64
    --windbg8.0, --windbg8.0_64
    --windbg8.1, --windbg8.1_64
    --windbg10, --windbg10_64
        Use windbg as debugger if available
    -c {cmdline}, --debugcmd={cmdline}
        Use {cmdline} to start the debugger
    -h, --help
        Print this help

usage 2: setdbg.py [-l|--list]
    List all debuggers found.
```

```
C:\> setdbg -l
available debugger(s):
vs2008          C:\VS2008\Common7\IDE\devenv.exe
vs2010          C:\VS2010\Common7\IDE\devenv.exe
vs2013          C:\VS2013\Common7\IDE\devenv.exe
vs2015(default) C:\VS2015\Common7\IDE\devenv.exe
windbg8.1       C:\Program Files (x86)\Windows Kits\8.1\Debuggers\x86\windbg.exe
windbg8.1_64    C:\Program Files (x86)\Windows Kits\8.1\Debuggers\x64\windbg.exe
windbg_64       C:\Program Files\Debugging Tools for Windows (x64)\windbg.exe
```

```
C:\> setdbg -e test1.exe test2.exe
# debugcmd: "C:\VS2015\Common7\IDE\devenv.com" /debugexe
enabled: test1.exe
enabled: test2.exe
```

```
C:\> setdbg -d test1.exe test2.exe
disabled: test1.exe
disabled: test2.exe
```
