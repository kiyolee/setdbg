# setdbg

Handy utility to set auto start-up debugger.

For Windows, registry setting "Image File Execution Options" is a well
known method to start some debugger automatically whenever certiain
named executable is executed.  Manually changing the setting using
regedit can be tidious though, especially so if needed to locate the
debugger first.

This utility locates all known debuggers from Microsoft and let you
enable/disable a set of executables to start the debugger of your
choice.
