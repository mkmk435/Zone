"""Esegue un exe sotto debugger e riporta l'indirizzo del primo fault.

Usage: python tmp/dbg_run.py <exe> [arg]
Stampa RVA del fault, i byte intorno all'indirizzo e, se si trova in .text,
l'istruzione decodificata.
"""
import ctypes
import ctypes.wintypes as wt
import sys

import pefile
from capstone import CS_ARCH_X86, CS_MODE_64, Cs

k32 = ctypes.WinDLL("kernel32", use_last_error=True)

DBG_CONTINUE = 0x00010002
DBG_EXCEPTION_NOT_HANDLED = 0x80010001
EXCEPTION_DEBUG_EVENT = 1
CREATE_PROCESS_DEBUG_EVENT = 3
LOAD_DLL_DEBUG_EVENT = 6
EXIT_PROCESS_DEBUG_EVENT = 5
DEBUG_ONLY_THIS_PROCESS = 0x00000002
DEBUG_PROCESS = 0x00000001
INFINITE = 0xFFFFFFFF


class STARTUPINFO(ctypes.Structure):
    _fields_ = [("cb", wt.DWORD), ("lpReserved", wt.LPWSTR), ("lpDesktop", wt.LPWSTR),
                ("lpTitle", wt.LPWSTR), ("dwX", wt.DWORD), ("dwY", wt.DWORD),
                ("dwXSize", wt.DWORD), ("dwYSize", wt.DWORD),
                ("dwXCountChars", wt.DWORD), ("dwYCountChars", wt.DWORD),
                ("dwFillAttribute", wt.DWORD), ("dwFlags", wt.DWORD),
                ("wShowWindow", wt.WORD), ("cbReserved2", wt.WORD),
                ("lpReserved2", ctypes.c_void_p), ("hStdInput", wt.HANDLE),
                ("hStdOutput", wt.HANDLE), ("hStdError", wt.HANDLE)]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [("hProcess", wt.HANDLE), ("hThread", wt.HANDLE),
                ("dwProcessId", wt.DWORD), ("dwThreadId", wt.DWORD)]


def main():
    exe = sys.argv[1]
    args = sys.argv[2:]
    exe_abs = __import__("os").path.abspath(exe)
    cmd = ctypes.create_unicode_buffer('"%s" %s' % (exe_abs, " ".join('"%s"' % a for a in args)))
    si = STARTUPINFO()
    si.cb = ctypes.sizeof(si)
    pi = PROCESS_INFORMATION()
    ok = k32.CreateProcessW(None, cmd, None, None, False,
                            DEBUG_ONLY_THIS_PROCESS, None, None,
                            ctypes.byref(si), ctypes.byref(pi))
    if not ok:
        print("CreateProcess fallita:", ctypes.get_last_error())
        return 1

    base = None
    fault = None
    code = None
    seen_first = False
    buf = (ctypes.c_char * 176)()
    events = 0
    while True:
        if not k32.WaitForDebugEvent(buf, 10000):
            print("timeout in attesa di eventi (err %d)" % ctypes.get_last_error())
            break
        event = ctypes.string_at(buf, 176)
        import struct
        ev_code, pid, tid = struct.unpack_from("<III", event, 0)
        union = event[16:]
        events += 1
        if ev_code != 6:      # non loggare i LOAD_DLL
            print("evento", ev_code, "pid", pid)
        if ev_code == CREATE_PROCESS_DEBUG_EVENT and base is None:
            base = struct.unpack_from("<Q", union, 24)[0]
            k32.CloseHandle(ctypes.c_void_p(struct.unpack_from("<Q", union, 0)[0]))
            k32.ContinueDebugEvent(pid, tid, DBG_CONTINUE)
        elif ev_code == EXCEPTION_DEBUG_EVENT:
            exc_code = struct.unpack_from("<I", union, 0)[0]
            exc_addr = struct.unpack_from("<Q", union, 16)[0]
            first = struct.unpack_from("<I", union, 152)[0]
            if exc_code == 0x80000003:      # breakpoint iniziale del loader
                k32.ContinueDebugEvent(pid, tid, DBG_CONTINUE)
                continue
            if fault is None:
                fault = exc_addr
                code = exc_code
                # stato dei registri e primi word dello stack
                ctx = (ctypes.c_char * 0x4D0)()
                import struct as _s
                _s.pack_into("<I", ctx, 0x30, 0x0010000B)
                if k32.GetThreadContext(pi.hThread, ctx):
                    regs = {}
                    for name, off in (("rax", 0x78), ("rcx", 0x80), ("rdx", 0x88),
                                      ("rbx", 0x90), ("rsp", 0x98), ("rbp", 0xA0),
                                      ("rsi", 0xA8), ("rdi", 0xB0), ("r8", 0xB8),
                                      ("r9", 0xC0), ("r10", 0xC8), ("r11", 0xD0),
                                      ("r12", 0xD8), ("r13", 0xE0), ("r14", 0xE8),
                                      ("r15", 0xF0), ("rip", 0xF8)):
                        regs[name] = _s.unpack_from("<Q", ctx, off)[0]
                    print("registri:", {k: hex(v) for k, v in regs.items()})
                    print("rva rax:", hex(regs["rax"] - base), "rip:", hex(regs["rip"] - base))
                    buf2 = (ctypes.c_char * 8 * 12)()
                    got = ctypes.c_size_t(0)
                    if k32.ReadProcessMemory(pi.hProcess, ctypes.c_void_p(regs["rsp"]),
                                             buf2, 8 * 12, ctypes.byref(got)):
                        words = _s.unpack("<12Q", ctypes.string_at(buf2, 8 * 12))
                        print("stack:", [hex(w - base) if w > base else hex(w) for w in words])
            if code == 0xC0000005 or code == 0xC0000096 or first == 0:
                print("eccezione non gestita, termino")
                k32.TerminateProcess(pi.hProcess, 1)
            k32.ContinueDebugEvent(pid, tid, DBG_EXCEPTION_NOT_HANDLED)
        elif ev_code == EXIT_PROCESS_DEBUG_EVENT:
            exit_code = struct.unpack_from("<I", union, 0)[0]
            k32.ContinueDebugEvent(pid, tid, DBG_CONTINUE)
            print("uscita con codice", hex(exit_code))
            break
        else:
            k32.ContinueDebugEvent(pid, tid, DBG_CONTINUE)

    k32.TerminateProcess(pi.hProcess, 1)
    k32.CloseHandle(pi.hThread)
    k32.CloseHandle(pi.hProcess)

    print("base immagine:", hex(base) if base else None)
    if fault is None:
        return 0
    print("eccezione:", hex(code), "a", hex(fault),
          "RVA", hex(fault - base) if base else "?")
    if not base:
        return 0
    pe = pefile.PE(exe)
    data = open(exe, "rb").read()
    rva = fault - base
    off = None
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            off = s.PointerToRawData + (rva - s.VirtualAddress)
            print("sezione", s.Name.rstrip(b"\x00").decode(errors="replace"))
            break
    if off is None:
        print("RVA non in una sezione")
        return 0
    raw = data[max(0, off - 32):off + 32]
    cs = Cs(CS_ARCH_X86, CS_MODE_64)
    cs.detail = True
    print("byte prima/dopo:")
    start = rva - 32
    for insn in cs.disasm(raw, start):
        mark = " <<<" if insn.address <= rva < insn.address + insn.size else ""
        print("  %#x %-24s %s%s" % (insn.address, insn.bytes.hex(), insn.mnemonic + " " + insn.op_str, mark))
    return 0


if __name__ == "__main__":
    sys.exit(main())
