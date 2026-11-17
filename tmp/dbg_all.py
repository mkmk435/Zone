import ctypes, ctypes.wintypes as wt, struct, sys
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
class SI(ctypes.Structure):
    _fields_=[("cb",wt.DWORD),("r",wt.LPWSTR),("d",wt.LPWSTR),("t",wt.LPWSTR),
              ("x",wt.DWORD),("y",wt.DWORD),("xs",wt.DWORD),("ys",wt.DWORD),
              ("xc",wt.DWORD),("yc",wt.DWORD),("f",wt.DWORD),("fl",wt.DWORD),
              ("sw",wt.WORD),("cb2",wt.WORD),("r2",ctypes.c_void_p),
              ("hi",wt.HANDLE),("ho",wt.HANDLE),("he",wt.HANDLE)]
class PI(ctypes.Structure):
    _fields_=[("hp",wt.HANDLE),("ht",wt.HANDLE),("pid",wt.DWORD),("tid",wt.DWORD)]
si=SI(); si.cb=ctypes.sizeof(si); pi=PI()
cmd=ctypes.create_unicode_buffer('"%s"' % sys.argv[1])
if not k32.CreateProcessW(None,cmd,None,None,False,2,None,None,ctypes.byref(si),ctypes.byref(pi)):
    print("CreateProcess fallita",ctypes.get_last_error()); raise SystemExit(1)
buf=(ctypes.c_char*176)(); events=[]
while True:
    if not k32.WaitForDebugEvent(buf,5000):
        print("timeout"); break
    ev=ctypes.string_at(buf,176); code,pid,tid=struct.unpack_from("<III",ev,0); u=ev[16:]
    if code==3:
        base=struct.unpack_from("<Q",u,24)[0]
        k32.ContinueDebugEvent(pid,tid,0x00010002)
    elif code==1:
        ec=struct.unpack_from("<I",u,0)[0]; ea=struct.unpack_from("<Q",u,16)[0]
        first=struct.unpack_from("<I",u,152)[0]
        events.append((hex(ec),hex(ea-base) if base and ea>base else hex(ea),first))
        k32.ContinueDebugEvent(pid,tid,0x80010001)
    elif code==5:
        ex=struct.unpack_from("<I",u,0)[0]
        print("exit", hex(ex))
        k32.ContinueDebugEvent(pid,tid,0x00010002)
        break
    else:
        k32.ContinueDebugEvent(pid,tid,0x00010002)
k32.TerminateProcess(pi.hp,1)
print("eccezioni:")
for e in events: print("  ", e)
