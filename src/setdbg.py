#!/usr/bin/env python3
#
# setdbg.py: https://github.com/kiyolee/setdbg.git
#
# MIT License
#
# Copyright (c) 2017-2020 Kelvin Lee
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

"""
usage 1: %(__file__)s [options] [-e|--enable {exe} ...] [-d|--disable {exe} ...]
    Enable/disable starting debugger for an executable upon execution.

options:
    --msvc6, --vc6
        Use MSVC6 as debugger if available.
    --vs(2003|2005|2008|2010|2012|2013|2015|2017|2019)
        Use Visual Studio as debugger if available.
    --windbg, --windbg_64
    --windbg8.0, --windbg8.0_64
    --windbg8.1, --windbg8.1_64
    --windbg10, --windbg10_64
        Use windbg as debugger if available.
    -c {cmdline}, --debugcmd={cmdline}
        Use {cmdline} to start the debugger.
    -h, --help
        Print this help.

usage 2: %(__file__)s [-l|--list]
    List all debuggers found.
"""

import sys
assert sys.platform == 'win32'

import os
import subprocess
import winreg

# __file__ is not defined after compiled with cx_Freeze
if '__file__' not in globals(): __file__ = sys.argv[0]

__program__ = os.path.basename(__file__)

__doc__ = __doc__ % globals()

IS_OS64BIT = (os.environ['PROCESSOR_ARCHITECTURE'] == 'AMD64')
IS_WOW64 = False

if not IS_OS64BIT:
    import ctypes
    def _is_wow64():
        k = ctypes.windll.kernel32
        p = k.GetCurrentProcess()
        i = ctypes.c_int()
        if k.IsWow64Process(p, ctypes.byref(i)):
            return i.value != 0
        return False
    IS_OS64BIT = IS_WOW64 = _is_wow64()
    del _is_wow64
    del ctypes
#print('# IS_OS64BIT=' + str(IS_OS64BIT) + ' IS_WOW64=' + str(IS_WOW64))

IFEO_KEY = r'Software\Microsoft\Windows NT\CurrentVersion\Image File Execution Options'

# To prevent serious trouble.
AVOID_LIST = [
   'cmd.exe',
   'conhost.exe',
   'conime.exe',
   'csrss.exe',
   'dwm.exe',
   'explorer.exe',
   'iexplore.exe',
   'lsm.exe',
   'procexp.exe',
   'regedit.exe',
   'rundll32.exe',
   'services.exe',
   'slsvc.exe',
   'smss.exe',
   'smsvchost.exe',
   'svchost.exe',
   'taskeng.exe',
   'taskmgr.exe',
   'wininit.exe',
   'winlogon.exe',
   ]

def get_program_files_directories():
    pf64 = ''
    if IS_OS64BIT:
        pf32 = os.environ['ProgramFiles(x86)']
        if IS_WOW64:
            # 32-bit python on 64-bit windows, cannot rely on ProgramFiles
            # which is the same as ProgramFiles(x86) for 32-bit binaries.
            x86_suffix = ' (x86)'
            if pf32.endswith(x86_suffix):
                pf64 = pf32[:-len(x86_suffix)]
            else:
                pf64 = ''
            del x86_suffix
        else:
            pf64 = os.environ['ProgramFiles']
    else:
        pf32 = os.environ['ProgramFiles']
    return pf32, pf64

VS_KEY = r'Software\Microsoft\VisualStudio'

# MSVC6 (32-bit only)
def get_msdev_exe():
    h, h2 = None, None
    try:
        wowkey = winreg.KEY_WOW64_32KEY if IS_OS64BIT else 0
        vs6_key = VS_KEY + r'\6.0'
        #print('#', vs6_key, wowkey)
        h = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, vs6_key, 0, wowkey | winreg.KEY_READ)
        h2 = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, vs6_key + r'\Setup', 0, wowkey | winreg.KEY_READ)
        instdir, t = winreg.QueryValueEx(h, 'InstallDir')
        assert t == winreg.REG_SZ
        commondir, t = winreg.QueryValueEx(h2, 'VsCommonDir')
        assert t == winreg.REG_SZ
        assert instdir.startswith(commondir) and (commondir[-1] == os.path.sep or instdir[len(commondir)] == os.path.sep)
        msdev_exe = os.path.join(commondir, 'msdev98', 'bin', 'msdev.exe')
        if os.path.isfile(msdev_exe):
            return msdev_exe
    except WindowsError as err:
        #print(err, file=sys.stderr)
        pass
    finally:
        if h:
            winreg.CloseKey(h)
            del h
        if h2:
            winreg.CloseKey(h2)
            del h2
    return None

# VS2003|2005|2008|2010|2012|2013|2015 (32-bit only)
def get_devenv_exe(vs_ver):
    h, h2 = None, None
    try:
        wowkey = winreg.KEY_WOW64_32KEY if IS_OS64BIT else 0
        vsX_key = VS_KEY + '\\' + vs_ver
        #print('#', suffix[1:], vsX_key, wowkey)
        h = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, vsX_key, 0, wowkey | winreg.KEY_READ)
        h2 = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, vsX_key + r'\Setup\VS', 0, wowkey | winreg.KEY_READ)
        instdir, t = winreg.QueryValueEx(h, 'InstallDir')
        assert t == winreg.REG_SZ
        devenv_exe, t = winreg.QueryValueEx(h2, 'EnvironmentPath')
        assert t == winreg.REG_SZ
        assert devenv_exe.startswith(instdir) and (instdir[-1] == os.path.sep or devenv_exe[len(instdir)] == os.path.sep)
        if os.path.isfile(devenv_exe):
            return devenv_exe
    except WindowsError as err:
        #print(err, file=sys.stderr)
        pass
    finally:
        if h:
            winreg.CloseKey(h)
            del h
        if h2:
            winreg.CloseKey(h2)
            del h2
    return None

def vswhere_get_devenv_exe(dbglist, pf32, pf64):
    vswhere = os.path.join(pf32, 'Microsoft Visual Studio', 'Installer', 'vswhere.exe')
    if not os.path.exists(vswhere):
        vswhere = os.path.join(pf64, 'Microsoft Visual Studio', 'Installer', 'vswhere.exe')
        if not os.path.exists(vswhere):
            return
    cmdp = subprocess.Popen([ vswhere, '-nologo' ], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    sout, serr = cmdp.communicate()
    if cmdp.returncode != 0 or serr:
        return
    it = iter(sout.decode('utf-8').split('\r\n'))
    try:
        while True:
            s = next(it).split(': ', 1)
            assert len(s) == 2
            if s[0] == 'instanceId':
                pp, pv = '', ''
                try:
                    while True:
                        s = next(it)
                        if not s: break
                        s = s.split(': ', 1)
                        assert len(s) == 2
                        if s[0] == 'productPath':
                            pp = s[1]
                        elif s[0] == 'catalog_productLineVersion':
                            pv = s[1]
                except StopIteration:
                    pass
                if pp and pv:
                    pv = 'vs' + pv
                    for i in range(1, 99):
                        vs_id = pv if i == 1 else pv + ('_%d' % i)
                        if not vs_id in dbglist:
                            dbglist[vs_id] = pp
                            break
    except StopIteration:
        pass

def get_debugger_list():
    dbglist = {}
    #
    # MSVC6 (32-bit only)
    #
    msdev_exe = get_msdev_exe()
    if msdev_exe: dbglist['msvc6'] = msdev_exe
    #
    # VS2003|2005|2008|2010|2012|2013|2015 (32-bit only)
    #
    for vs_ver, vs_id in [ ( '7.0', 'vs2003' ),
                           ( '7.1', 'vs2003' ),
                           ( '8.0', 'vs2005' ),
                           ( '9.0', 'vs2008' ),
                           ( '10.0', 'vs2010' ),
                           ( '11.0', 'vs2012' ),
                           ( '12.0', 'vs2013' ),
                           ( '14.0', 'vs2015' ),
                           ]:
        devenv_exe = get_devenv_exe(vs_ver)
        if devenv_exe: dbglist[vs_id] = devenv_exe
    #
    pf32, pf64 = get_program_files_directories()
    #
    # VS2017 or later (32-bit only)
    #
    vswhere_get_devenv_exe(dbglist, pf32, pf64)
    #
    # windbg for Windows 8 or later (32-bit and 64-bit)
    #
    pf = [ pf32 ]
    if pf64: pf += [ pf64 ]
    for win_ver in [ '8.0', '8.1', '10' ]:
        for arch, dbgsuffix in [ ( 'x86', '' ), ( 'x64', '_64' ) ]:
            for p in pf:
                windbg_exe = os.path.join(p, 'Windows Kits', win_ver, 'Debuggers', arch, 'windbg.exe')
                if os.path.isfile(windbg_exe):
                    dbglist['windbg' + win_ver + dbgsuffix] = windbg_exe
                    break
    #
    # windbg for Windows 7 or before
    #
    # windbg (64-bit)
    if pf64:
        for p in [ 'Debugging Tools for Windows (x64)', 'Debugging Tools for Windows' ]:
            windbg_exe = os.path.join(pf64, p, 'windbg.exe')
            if os.path.isfile(windbg_exe):
                dbglist['windbg_64'] = windbg_exe
                break
    # windbg (32-bit)
    if pf32:
        for p in [ 'Debugging Tools for Windows (x86)', 'Debugging Tools for Windows' ]:
            windbg_exe = os.path.join(pf32, p, 'windbg.exe')
            if os.path.isfile(windbg_exe):
                dbglist['windbg'] = windbg_exe
                break
    return dbglist

def get_dbg_id_prioritized(debuggers):
    dbg_ids = list(debuggers.keys())
    def _dbg_id_to_key(dbg_id):
        x = 0 if dbg_id.startswith('vs') else ( -1 if dbg_id.startswith('windbg') else -2 )
        if x == 0 and '_' in dbg_id:
            s = dbg_id.rsplit('_', 1)
            try:
                return x, s[0], 0, -int(s[1])
            except ValueError:
                pass
        elif x == -1:
            if dbg_id.endswith('_64'):
                return x, dbg_id[:-3], 0, 0
            else:
                return x, dbg_id, -1, 0
        return x, dbg_id, 0, 0
    dbg_ids.sort(key=_dbg_id_to_key, reverse=True)
    return dbg_ids

def default_debugger(debuggers):
    try:
        return get_dbg_id_prioritized(debuggers)[0]
    except IndexError:
        pass
    return ''

def print_debuggers(debuggers, dbgdef):
    dk = list(debuggers.keys())
    if dk:
        print('Available %s:' % ('debuggers' if len(dk) > 1 else 'debugger'))
        def dbgkey(k):
            return k + '(default)' if k == dbgdef else k
        dk.sort()
        kl = [ ( k, dbgkey(k) ) for k in dk ]
        ml = len(max(kl, key=lambda k: len(k[1]))[1]) + 1
        for k, krem in kl:
            print('%-*s%s' % ( ml, krem, debuggers[k] ))
    else:
        print('No debugger found.')

def add_exe(exelist, arg):
    for e in arg.split(','):
        exe = os.path.split(e)[1].lower()
        bn, ext = os.path.splitext(exe)
        if ext != '.exe':
            exe = bn + '.exe'
        if not exe in exelist and not exe in AVOID_LIST:
            exelist.append(exe)
        else:
            print('# ignore:', exe)

def key_is_empty(hkey):
    try:
        winreg.EnumKey(hkey, 0)
        has_subkey = True
    except WindowsError as err:
        has_subkey = False
    try:
        winreg.EnumValue(hkey, 0)
        has_value = True
    except WindowsError as err:
        has_value = False
    return not has_subkey and not has_value

def main():
    if not sys.argv[1:]:
        print(__doc__)
        return 255

    debuggers = get_debugger_list()
    #print('# debuggers:', debuggers)
    dbgdef = default_debugger(debuggers)

    dbg_opts = list(debuggers.keys())
    dbg_opts += [ i[2:] for i in dbg_opts if i.startswith('vs') ]
    if 'msvc6' in debuggers: dbg_opts += [ 'vc6' ]

    enable_list = []
    disable_list = []
    debugcmd = ''
    dbgsel = ''
    to_enable = True

    import getopt
    args = []
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'e:d:c:lh',
                                    [ 'enable=', 'disable=',
                                      'debugcmd=',
                                      'list', 'help',
                                      ] + dbg_opts)
    except getopt.error as err:
        print(err, file=sys.stderr)
        return 255

    for opt, val in opts:
        if opt in ( '-e', '--enable' ):
            add_exe(enable_list, val)
            to_enable = True
        elif opt in ( '-d', '--disable' ):
            add_exe(disable_list, val)
            to_enable = False
        elif opt in ( '-c', '--debugcmd' ):
            debugcmd = val
        elif opt in ( '--msvc6', '--vc6' ):
            assert not dbgsel
            dbgsel = 'msvc6'
        elif (opt.startswith('--') and (opt[2:] in debuggers)):
            assert not dbgsel
            dbgsel = opt[2:]
        elif (opt.startswith('--') and ('vs' + opt[2:] in debuggers)):
            assert not dbgsel
            dbgsel = 'vs' + opt[2:]
        elif opt in ( '-l', '--list' ):
            print_debuggers(debuggers, dbgdef)
            return 1
        elif opt in ( '-h', '--help' ):
            print(__doc__)
            return 255

    for a in args:
        if a in ( '-e', '--enable' ):
            to_enable = True
        elif a in ( '-d', '--disable' ):
            to_enable = False
        else:
            if to_enable:
                add_exe(enable_list, a)
            else:
                add_exe(disable_list, a)

    if enable_list and not debugcmd:
        if dbgsel:
            if not dbgsel in debuggers:
                if dbgsel.endswith('_64'):
                    if dbgsel[:-3] in debuggers: dbgsel = dbgsel[:-3]
                else:
                    if dbgsel + '_64' in debuggers: dbgsel += '_64'
        else:
            dbgsel = dbgdef
        if dbgsel in debuggers:
            dbgexe = debuggers[dbgsel]
            p, e = os.path.split(dbgexe)
            e = e.lower()
            # Mysteriously need the corresponding .com executable to work.
            if e == 'devenv.exe':
                devenv_com = os.path.join(p, 'devenv.com')
                if os.path.isfile(devenv_com):
                    debugcmd = '"' + devenv_com + '" /debugexe'
                else:
                    debugcmd = '"' + dbgexe + '" /debugexe'
            elif e == 'msdev.exe':
                msdev_com = os.path.join(p, 'msdev.com')
                if os.path.isfile(msdev_com):
                    debugcmd = '"' + msdev_com + '"'
                else:
                    debugcmd = '"' + dbgexe + '"'
            else:
                debugcmd = '"' + dbgexe + '"'
        else:
            print('Debugger selection %s not found.' % dbgsel)
            print_debuggers(debuggers, dbgdef)
            return 1

    #print('# enable_list:', enable_list)
    #print('# disable_list:', disable_list)

    hIFEO = None
    if disable_list or enable_list:
        try:
            # Both 32 and 64 bit hives are symbolic linked.
            hIFEO = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, IFEO_KEY, 0, winreg.KEY_READ)
        except WindowsError as err:
            hIFEO = None

    if hIFEO:
        if disable_list:
            for d in disable_list:
                h = None
                try:
                    h = winreg.OpenKey(hIFEO, d, 0, winreg.KEY_READ | winreg.KEY_WRITE)
                    winreg.DeleteValue(h, 'Debugger')
                    print('disabled:', d)
                except WindowsError as err:
                    if not h and err.errno == 2:
                        print('already disabled:', d)
                    else:
                        print(err)
                        print('failed to disable:', d)
                finally:
                    if h:
                        is_empty = key_is_empty(h)
                        winreg.CloseKey(h)
                        del h
                        if is_empty:
                            #print('# %s is empty' % d)
                            try:
                                winreg.DeleteKey(hIFEO, d)
                            except WindowsError as err:
                                #print(err, file=sys.stderr)
                                pass

        if enable_list:
            print('# debugcmd:', debugcmd)
            for e in enable_list:
                h = None
                try:
                    h = winreg.CreateKey(hIFEO, e)
                    winreg.SetValueEx(h, 'Debugger', 0, winreg.REG_SZ, debugcmd)
                    print('enabled:', e)
                except WindowsError as err:
                    print(err)
                    print('failed to enable:', e)
                finally:
                    if h:
                        winreg.CloseKey(h)
                        del h

        winreg.CloseKey(hIFEO)

    return 0

if __name__ == '__main__':
    sys.exit(main())

#---eof---
