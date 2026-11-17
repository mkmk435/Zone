import sys, struct
sys.path.insert(0, "tmp")
import make_test_pe as mk
mk.SOURCE = "mov eax, 42\n ret\n"
mk.build("tmp/test_min.exe")
