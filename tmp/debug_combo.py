import sys
sys.path.insert(0, r"C:\Users\ubu\Desktop\Zone")
from pobf import Zone
import llm_data
from llm_technique import LLMOptions
path=r"C:\Users\ubu\Desktop\Zone\original_pl\x64\windows_x64_messagebox.bin"
z=Zone(path)
opts=LLMOptions(technique="data",arch="x64",mock_response="tmp/data_mock_msgbox.json",retries=1)
res=llm_data.run_data(lambda: Zone(path), z.raw_code, "x64", opts)
z=res.zone
z.data_refs_finalized=False
z.create_jmp_table(); z.create_label_table()
z.equal_instructions()
z.update_label_table()
for f in z.data_ref_fixups:
    ins=f["instr"]
    print("pre", ins.new_instruction.address, ins.new_instruction.bytes.hex(), ins.new_instruction.op_str)
z.finalize_data_refs()
for f in z.data_ref_fixups:
    ins=f["instr"]
    print("post", ins.new_instruction.address, ins.new_instruction.bytes.hex(), ins.new_instruction.op_str)
print("instr list after finalize")
for ins in z.instructions:
    if 0xe0 <= ins.new_instruction.address <= 0xf0:
        print(ins.new_instruction.address, ins.new_instruction.bytes.hex(), ins.new_instruction.op_str, id(ins))
