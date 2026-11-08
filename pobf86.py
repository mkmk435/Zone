from capstone import *   #e' un disassembler
from keystone import *   #e' un assembler
import sys
import pefile
import time
# import lief
import os
import json
import hashlib
import re
import random
from capstone import x86_const
import zone_utils
import increase_text
import symbolic_payload_coverage
import traceback
# import asmjit
import subprocess

#blablablableblebleblublublublublublublublublublublublublu

# una classe che rappresenta un istruzione in tutte le sue forme, attuale, vecchia, originale, precedente e prossima
# a class that represents an instruction in all its forms, current, old, original, previous and next
class Instruction:
    def __init__(self,new_instruction,old_instruction,original_instruction,prev_instruction,next_instruction):
        self.new_instruction = new_instruction
        self.old_instruction = old_instruction
        self.original_instruction = original_instruction
        self.prev_instruction = prev_instruction
        self.next_instruction = next_instruction
        self.address_history = []
        self.bad_expanded = False
        self.pii_group = False
        # set when this instruction is a rewritten reference to extracted data
        self.data_ref_fixup = None
        # set on instructions that must not be turned into other code
        self.protected = False




class Zone:

    def __init__(self, file):


        # inizializzo il disassembler
        # initialize the disassembler
        self.cs = Cs(CS_ARCH_X86, CS_MODE_32)  #pip install capstone==5.0.0.post1 ONLY INSTALL THIS VERSION. ON OTHER VERSIONS IT DOES NOT WAR skipdataK
        self.cs.detail = True

        #utile per skippare dati inutili nella .text (tipo stringhe o tabelle di jump)
        # useful for skipping useless data in the .text (like strings or jump
        self.cs.skipdata = True 



        #list of registers 
        # self.reg_list32 = ['eax','ebx','ecx','edx','esi','edi','ebp','esp','r8d','r9d','r10d','r11d','r12d','r13d','r14d','r15d']
        # self.reg_list32 = ['eax','ebx','ecx','edx','esi','edi','ebp','esp']
        self.reg_list32 = ['eax','ebx','ecx','edx','esi','edi']

        self.reg_list16 = ['ax','bx','cx','dx','si','di','bp','sp']
        self.reg_list8 = ['al','bl','cl','dl','ah','bh','ch','dh']
        self.reg_lists = [self.reg_list32,self.reg_list16,self.reg_list8]

        # list of all the possible nop instructions
        # self.no_ops_templates = ['nop','sub','add','mov','lea','push','or','xor','and','inc','sar','shr','shl','rcl','rcr', 'jmp']
        self.no_ops_templates = ['nop','sub','add','mov','lea','or','xor','and','inc','sar','shr','shl','rcl','rcr', 'jmp']

        self.file = file

        self.bogus_probability = 20
        # inizializzo l'assembler
        # initialize the assembler
        self.ks = Ks(KS_ARCH_X86, KS_MODE_32)
        
        # i don't remember
        self.push_mov = False




        # blocks for future implementation of bogus control flow
        self.instr_blocks = []
        self.block_size = 7
        self.last_chosen_reg = None


        # lista di tuple (istruzione, indirizzo) per tutte le jmp/call che puntano a indirizzi dentro la .text
        # list of tuples (instruction, address) for all the jmp/call that point to addresses inside the .text, (I use only short for now)
        self.short_label_table = []
        self.far_label_table = []

        #lista dinamica globale di istruzioni
        # dynamic global list of instructions
        self.instructions = []

        #lista di jump table (causate da switch-cases)
        # list of jump tables (caused by switch-cases)
        self.jump_table = []
        
        # lista di tuple (start,end) per le jump table, utile per verificare se un indirizzo e' dentro una jump table
        # list of tuples (start,end) for the jump tables, useful to check if an address is inside a jump table
        self.start_end_table = []
        self.brain_blocks = []
        #dizionario di istruzioni, molto utile dal punto di vista delle performance(tempo di accesso costante)
        #  dictionary of instructions, very useful from a performance point of view (constant access time)
        self.instr_dict = {}
        # instructions inside inline ASCII/hash data must not be morphed
        self.data_instruction_ids = set()
        self.data_ranges32 = []
        self.nop_skip_ids = set()
        # ductionary like instr_dict but with key updated to the old_instruction(not the original)
        self.updated_instr_dict = {}

        self.payload_size = 0
        
        self.stub_address = 0
        self.stub_size = 0
        self.mem_address = 0
        self.counter_address = 0
        self.instr_mapping = []
        self.stub2_address = 0
        self.stub2_bytearr = 0
        self.stub2_size = 0

        self.do_not_touch = []

        self.pii_enabled = False

        self.init_address = 0
        self.wrap_instruction_num = 5


        with open(self.file, "rb") as f:
            self.raw_code = f.read()
            f.close()


        # lunghezza del codice originale
        self.original_code_length = len(self.raw_code)
        self.equal_instructions_substitutions = 0
        self.base_address = 0

        self.nops_addedd = 0

        self.bytes_to_add = []

        # data layer state (same interface as pobf.py)
        self.data_xrefs = []
        self.data_sections = []

        # data-extraction state (opt-in, see --extract-data)
        self.extracted_data = []
        self.data_ref_fixups = []
        self.final_data_blob = None
        self.final_data_pad = b''
        self.final_code_len = 0
        self.data_refs_finalized = False

        # kept for write_file(): a truncated sweep must not lose the tail
        self.sweep_coverage = 0
        self.sweep_tail = b''
        self.morph_applied = False



        #con questo ciclo apro il file instr.txt e ci scrivo le istruzioni disassemblate
        # just write instructions to .txt for debugging
        with open('instr_payload.txt', 'r+') as f:

            for i in self.cs.disasm(self.raw_code, 0):
                
                # creo un oggetto Instruction e lo aggiungo alla lista di istruzioni
                # new,old,original = i. prev and next will be assigned later
                instruction = Instruction(i,i,i,None,None) 
                instruction.address_history.append(i.address)
                self.instructions.append(instruction)


                #questo dizionario ci potro' accedere con la chiave dell' indirizzo originale
                self.instr_dict[i.address] = instruction
                #questo dizionario ci potro' accedere con la chiave dell' precedente, e' molto utile in futuro
                # this dictionary can be accessed with the key of the previous address, it is very useful in the future
                self.updated_instr_dict[i.address] = instruction

            
                # just to write to file
                stringa = f"{hex(i.address)} {i.bytes} {i.size}  {i.mnemonic}  {i.op_str}\n"
                last_address = i.address
                last_size = i.size
                f.write(stringa)

        

        print("FINITO DI DISASSEMBLARE")
        #self.cs.skipdata = False

        # Capstone's skipdata support is broken in some versions (5.0.1):
        # the linear sweep can stop before the end of the payload. Keep the
        # unscanned tail so a plain write still reproduces the input.
        self.sweep_coverage = sum(len(i.new_instruction.bytes)
                                  for i in self.instructions)
        self.sweep_tail = self.raw_code[self.sweep_coverage:]

        #assegno i prev_instruction e next_instruction
        # assign prev_instruction and next_instruction
        for x,instr in enumerate(self.instructions):
            instr.new_bytes = instr.new_instruction.bytes

            if x == 0:
                continue
            instr.prev_instruction = self.instructions[x-1]
            if x == len(self.instructions)-1:
                continue
            instr.next_instruction = self.instructions[x+1]



    # Per ogni istruzione JMP o CALL riferite ad elementi dentro la .text creo una tabella di label del tipo (istruzione,indirizzo a cui salto)
    # For each JMP or CALL instruction referring to elements inside the .text I create a label table of the type (instruction, address to which I jump)
    def create_label_table(self):
        print("CREO LABEL TABLE")
        for instr in self.instructions:
            try:
                # always check if the instruction is inside a jump table, and skip it if it is
                inside_jmp_table = self.check_if_inside_jmp_table(instr.original_instruction.address)
                if inside_jmp_table == True:
                    continue
                
                if instr.new_instruction.mnemonic == '.byte':
                    continue
                # checka se JUMP/CALL/LOOP
                if (x86_const.X86_GRP_JUMP in instr.new_instruction.groups) or (x86_const.X86_GRP_CALL in instr.new_instruction.groups) or (instr.new_instruction.mnemonic == 'loop'):
                    if ('ptr' not in instr.new_instruction.op_str) and instr.new_instruction.operands[0].type != x86_const.X86_OP_REG:
                        if instr.new_instruction.mnemonic == 'jrcxz':
                            print("JRCXZ")
                            # time.sleep(2)
                        elif instr.new_instruction.mnemonic == 'loop':
                            print("LOOP")
                            # time.sleep(2)
                        # addr = instr.new_instruction.address + 2
                        addr = zone_utils.estrai_valore(instr.new_instruction.op_str)
                        target = self.instr_dict.get(addr)
                        if target is None:
                            # target is inline data / not a decoded instruction
                            continue
                        self.short_label_table.append((instr, target))
            except Exception as e:
                print("Errore in create_label_table(): ",e)
                print("Indirizzo: ",hex(instr.new_instruction.address))
                print("stringa: ",instr.new_instruction.mnemonic + '  ' + instr.new_instruction.op_str)

                traceback.print_exc()
                continue


        # self.short_label_table.sort()

    def generate_assembly_tautology(self):
    # List of common registers (excluding esp/ebp for simplicity)
        # registers = random.choice(self.reg_list32)
        # print("REGISTERS: ",registers)
        reg = random.choice(self.reg_list32)
        while True:
            if reg != self.last_chosen_reg:
                break
            reg = random.choice(self.reg_list32)
        self.last_chosen_reg = reg
        print("REG: ",reg)
        # Generate a random immediate value (for example, between 0 and 255)
        imm = random.randint(0, 255)
        
        # Choose a random pattern (from 1 to 15)
        pattern = random.randint(1,12)
        code = ""

        # per testing
        
        if pattern == 1:
            # Pattern 1: mov reg, imm; cmp reg, imm
            code = f"pushfd;push {reg};mov {reg}, {imm};cmp {reg}, {imm};pop {reg};popfd"
        elif pattern == 2:
            # Pattern 2: cmp reg, reg
            code = f"pushfd;cmp {reg}, {reg};popfd"
        elif pattern == 3:
            # Pattern 3: mov reg, imm; add reg, 0; cmp reg, imm
            code = f"pushfd;push {reg};mov {reg}, {imm};add {reg}, 0;cmp {reg}, {imm}; pop {reg};popfd"
        elif pattern == 4:
            # Pattern 4: mov reg, imm; sub reg, 0; cmp reg, imm
            code = f"pushfd;push {reg};mov {reg}, {imm};sub {reg}, 0;cmp {reg}, {imm}; pop {reg};popfd"
        elif pattern == 5:
            # Pattern 5: push imm; pop reg; cmp reg, imm
            code = f"pushfd;push {reg};push {imm};pop {reg};cmp {reg}, {imm}; pop {reg};popfd"
        elif pattern == 6:
            # Pattern 6: sub reg, reg; cmp reg, 0
            code = f"pushfd;push {reg};sub {reg}, {reg};cmp {reg}, 0; pop {reg};popfd"
        elif pattern == 7:
            # Pattern 7: xor reg, reg; cmp reg, 0
            code = f"pushfd;push {reg}; xor {reg}, {reg};cmp {reg}, 0; pop {reg};popfd"
        elif pattern == 8:
            # Pattern 9: mov reg, imm; neg reg; neg reg; cmp reg, imm
            code = f"pushfd;push {reg}; mov {reg}, {imm};neg {reg};neg {reg};cmp {reg}, {imm}; pop {reg};popfd"
        elif pattern == 9:
            # Pattern 10: mov reg, imm; or reg, 0; cmp reg, imm
            code = f"pushfd;push {reg}; mov {reg}, {imm};or {reg}, 0;cmp {reg}, {imm}; pop {reg};popfd"
        elif pattern == 10:
            # Pattern 11: mov reg, imm; and reg, 0xFFFFFFFF; cmp reg, imm
            code = f"pushfd;push {reg};mov {reg}, {imm};and {reg}, 0xFFFFFFFF;cmp {reg}, {imm}; pop {reg};popfd"
        elif pattern == 11:
            # Pattern 12: mov reg, imm; lea reg, [{reg}+0]; cmp reg, imm
            code = f"pushfd;push {reg};mov {reg}, {imm};lea {reg}, [{reg}+0];cmp {reg}, {imm}; pop {reg};popfd"
        elif pattern == 12:
            # Pattern 13: mov reg, imm; test reg, reg
            code = f"pushfd;push {reg};mov {reg}, {imm};test {reg}, {reg}; pop {reg};popfd"
        else:
            code = "nop"
        
        return code
    

    def bogus_control_flow(self):
        # SOLUZIONE ULTRA TEMPORANEA
        last_modification = 0
        re_iterate = True
        inserted_instr = 0

        while re_iterate == True:
            re_iterate = False

            self.update_instr()
            self.update_label_table()
            
            for num_instr,instr in enumerate(self.instructions):
                probability = random.randint(0,100)

                # print("NUM_INSTR: ",num_instr)
                # print("LAST_MODIFICATION: ",last_modification)
                # print("INSERTED_INSTR: ",inserted_instr)
                if num_instr < (last_modification + inserted_instr):
                    continue
                if id(instr) in self.data_instruction_ids:
                    continue
                if (instr.next_instruction is not None
                        and id(instr.next_instruction) in self.data_instruction_ids):
                    continue
                if instr.new_instruction.address < getattr(self, "nop_min_address", 0):
                    continue
                if probability < self.bogus_probability:
                    re_iterate = True
                    inserted_instr = 0

                    # trash_block = bytearray()

                    block_size = random.randint(5,10)

                    # appendi popfd come pr
                    # for i in range(block_size):
                    #     trash_block.append(0x90)

                    code = self.generate_assembly_tautology()

                    if code == "nop":
                        continue
                    asm, _ = self.ks.asm(code, instr.new_instruction.address + instr.new_instruction.size)
                    asm = bytearray(asm)

                    NOP_NUM = random.randint(2,5)

                    code = code + ';je ' + hex(instr.new_instruction.address + instr.new_instruction.size + len(asm) + len(asm) + 2 + NOP_NUM*1)
                    
                    print("CODE: ",code)
                    last_modification = num_instr

                    asm2, _ = self.ks.asm(code, instr.new_instruction.address + instr.new_instruction.size + len(asm))
                    asm2 = bytearray(asm2)
                    for i in range(NOP_NUM):
                        # random_byte = random.randint(0,255)
                        asm2.append(0x90)
                    tmp_inserted_instr = 0
                    for x,i in enumerate(self.cs.disasm(asm2, instr.new_instruction.address + instr.new_instruction.size)):
                        new_instr = Instruction(i,i,i,None,None)
                        new_instr.address_history.append(i.address)
                        self.insert_instruction(num_instr + x,new_instr)
                        if i.mnemonic == 'je':
                            # Keep the je target in the label table: later
                            # random insertions must repatch it.
                            self.short_label_table.append((new_instr, instr))
                        tmp_inserted_instr +=  1
                    # faccio break perche' dovro' fare la reiterazione
                    inserted_instr = tmp_inserted_instr
                    break
        ## DA RIFARE IN MODO GIUSTO
        # num_instr = 0
        # last_modification = 0
        # inserted_instr = 0
        # # index of last instruction
        # last_instruction_index = len(self.instructions) - 1 

        # new_index = 0
        # try:
        #     while True:
        #         instr = self.instructions[num_instr]
        #         probability = random.randint(0,100)

        #         if num_instr >= last_instruction_index:
        #             break

        #         if (num_instr - last_modification) < inserted_instr:
        #             num_instr += 1
        #             # print("Num_instr: ",num_instr)
        #             # print("inserted_instr: ",inserted_instr)
        #             continue
        #         if probability <= 10:
        #             inserted_instr = 0
        #             self.update_instr()
        #             self.update_label_table()
        #             trash_block = bytearray()

        #             block_size = random.randint(5,10)

        #             # appendi popfd come pr
        #             for i in range(block_size):
        #                 trash_block.append(0x90)

        #             code = self.generate_assembly_tautology()

        #             if code == "nop":
        #                 continue
        #             asm, _ = self.ks.asm(code, instr.new_instruction.address + instr.new_instruction.size)
        #             asm = bytearray(asm)

        #             NOP_NUM = random.randint(2,5)

        #             code = code + ';je ' + hex(instr.new_instruction.address + instr.new_instruction.size + len(asm) + len(asm) + 2 + NOP_NUM*1)
                    
        #             print("CODE: ",code)

        #             asm2, _ = self.ks.asm(code, instr.new_instruction.address + instr.new_instruction.size + len(asm))
        #             asm2 = bytearray(asm2)
        #             for i in range(NOP_NUM):
        #                 asm2.append(0x90)
        #             for x,i in enumerate(self.cs.disasm(asm2, instr.new_instruction.address + instr.new_instruction.size)):
        #                 new_instr = Instruction(i,i,i,None,None)
        #                 new_instr.address_history.append(i.address)
        #                 self.insert_instruction(num_instr + x,new_instr)
        #                 inserted_instr +=  1
        #                 num_instr += 1
        #                 last_instruction_index += 1
        #             last_modification = num_instr
        #             continue
        #         num_instr += 1
        # except Exception as e:
        #     print("Errore in bogus_control_flow(): ",e)
        #     print("Indirizzo: ",hex(instr.new_instruction.address))
        #     print("stringa: ",instr.new_instruction.mnemonic + '  ' + instr.new_instruction.op_str)
        #     traceback.print_exc()
        #     pass`

    # after every change in the instructions list, I have to update the instr_dict
    # the update is made simply by iterating over the instructions list and updating the instr_dict and updating addresses of instructions
    def update_instr(self):
        print("UPDATE INSTR")
        
        new_instr_dict = {}
        for x,i in enumerate(self.instructions):
            try:

                if x == 0:
                    continue
                if i.prev_instruction is None:
                    continue
                addr = i.prev_instruction.new_instruction.address + len(i.prev_instruction.new_instruction.bytes)

                old_addr = i.old_instruction.address

                for n in self.cs.disasm(i.new_instruction.bytes,addr):
                    i.old_instruction = i.new_instruction

                    # also remember to update the dictionary
                    new_instr_dict[i.old_instruction.address] = i
                    i.address_history.append(n.address)

                    i.new_instruction = n

            except Exception as e:
                print("Errore in update_instr(): ",e)
                print('Indirizzo: ',hex(i.new_instruction.address))
                continue
        # also remember to update the dictionary
        self.updated_instr_dict = new_instr_dict
        with open('dict.txt', 'r+') as f:
            for key in self.updated_instr_dict:
                stringa = f"{hex(key)} {hex(self.updated_instr_dict[key].new_instruction.address)}\n"
                f.write(stringa)


    # just print the instructions to a file
    def print_instructions(self):
        with open('instr_payload2.txt', 'r+') as f:

            for x,i in enumerate(self.instructions):
                stringa  = f"{hex(i.new_instruction.address)} {i.new_instruction.bytes} {len(i.new_instruction.bytes)}  {i.new_instruction.mnemonic}  {i.new_instruction.op_str}\n"
                f.write(stringa)

    # this is some serious fucked up stuff
    # patch all JMP and CALL after some modifications




    def update_label_table(self):
        print("UPDATE LABEL TABLE")

        # if during patching some JMP or CALL becomes bigger (example 3 byte --> 5 byte)
        #   i need to re iterate the all patching process
        re_iterate = True
        num_iterazioni = 0

        do_not_touch_instr = []
        inserted_instructions = False
        while re_iterate == True:
            print("ITERANDO: num_iterazioni: ",num_iterazioni)
            # always update instructions beforse patching them, otherwise instructions addresses will be broken
            self.update_instr()
            re_iterate = False
            num_iterazioni += 1
            # try:

            # iterate the list of jmp/call instructions
            for entry in self.short_label_table:
                try:

                    # various checks 
                    if self.check_if_inside_jmp_table(entry[0].new_instruction.address) == True:
                        continue

                    if (x86_const.X86_GRP_JUMP not in entry[0].new_instruction.groups) and (x86_const.X86_GRP_CALL not in entry[0].new_instruction.groups) and (entry[0].new_instruction.mnemonic != 'loop'):
                        continue

                    if (entry[0].new_instruction.operands[0].type == x86_const.X86_OP_REG):
                        continue
                    # check if it is a jmp to far stuff (improbable), do not patch it here because it is patched in adjust_out_text_reference()
                    if 'ptr' in entry[0].new_instruction.op_str:
                        continue



                        # time.sleep(2)

                    # extract the jmp address from the string (yea i love python, so easy)
                    old_jump_address = zone_utils.estrai_valore(entry[0].new_instruction.op_str)


                    if old_jump_address == 0:
                        print(entry[0].new_instruction.mnemonic, entry[0].new_instruction.op_str)
                    


                    jmp_addr = zone_utils.estrai_valore(entry[0].new_instruction.op_str)
                    jmp_addr_ptr = entry[1].new_instruction.address
                    
                    index = self.instructions.index(entry[0])

                    # check if the jmp address is right
                    if jmp_addr != jmp_addr_ptr:

                        original_length = len(entry[0].new_instruction.bytes)

                        # assemblate with a string the new instruction
                        str_instr = f"{entry[0].new_instruction.mnemonic} {hex(jmp_addr_ptr)}"

                        bytes_arr = None
                        ################checko se ci sono istruzioni infami pezze di mmerda cacone ridicole#########
                        if (entry[0].new_instruction.mnemonic == 'jrcxz' or entry[0].new_instruction.mnemonic == 'loop'):

                            # bytes_arr = bytearray(asm(str_instr, arch='amd64'))
                            # bytes_arr = asm(str_instr, arch='x86_64')

                            print("JRCXZ/LOOP: \n")

                        ######################################################

                        if entry[0].new_instruction.mnemonic == 'jrcxz':
                            diff = abs(jmp_addr_ptr - entry[0].new_instruction.address)
                            print(f"###############\nDIFF: {diff}\n###############\n")
                            if diff > 120:
                                
                                print("\n###########################################\n")
                                print("DIFF > 120!!\n")
                                print(f"DIFF: {diff}\n")
                                print("PLEASE RESTART THE SOFTWARE UNTIL DIFF < 120\n")
                                print("EXITING...............\n")
                                print("###########################################\n")

                                # Restart with the *same* command line. The old
                                # version only passed sys.argv[0] and sys.argv[1],
                                # losing --extract-data, -eq, -o, etc.
                                try:
                                    restarts = int(os.environ.get(
                                        "POBF_JRCXZ_RESTARTS", "0"))
                                except ValueError:
                                    restarts = 0
                                if restarts >= 20:
                                    print("Too many restarts (jrcxz distance "
                                          "still > 120); aborting.")
                                    sys.exit(1)
                                env = os.environ.copy()
                                env["POBF_JRCXZ_RESTARTS"] = str(restarts + 1)
                                command = ([sys.executable,
                                            os.path.abspath(sys.argv[0])]
                                           + sys.argv[1:])
                                print("RESTARTING:",
                                      subprocess.list2cmdline(command))
                                result = subprocess.run(command, env=env)
                                sys.exit(result.returncode)
                                # start()
                                
                            #     time.sleep(2)
                            #     exit(0)
                            # time.sleep(2)
                        asm, _ = self.ks.asm(str_instr, entry[0].new_instruction.address)
                        bytes_arr = bytearray(asm)

                        new_length = len(bytes_arr)
                        # check if the new assembled instruction is different in size from the old one
                        if original_length != new_length:
                            # if the new size is lower just insert NOPs to pad
                            if original_length > new_length:
                                if self.pii_enabled == True:
                                
                                    print("🚨🚨NINONINO NINONINO POLIZIA DEL DEBUGGING ZIOPERA🚨🚨")
                                    if entry[0].new_instruction.operands[0].type == x86_const.X86_OP_IMM:
                                        offset = (entry[0].new_instruction.address + len(entry[0].new_instruction.bytes)) - entry[1].new_instruction.address
                                        print("OPERAND: IMM")
                                    elif entry[0].new_instruction.operands[0].type == x86_const.X86_OP_MEM:
                                        offset = entry[1].new_instruction.address
                                    else:
                                        offset = entry[0].new_instruction.operands[0].imm - entry[1].new_instruction.address
                                    opcode = entry[0].new_instruction.opcode
                                    original_opcode = []
                                    for byte in opcode:
                                        if byte != 0x00:
                                            original_opcode.append(byte)
                                    original_op_len = len(original_opcode)
                                    # convert original_opcode array to an int
                                    original_opcode = int.from_bytes(original_opcode, byteorder='little')
                                    print("original_opcode: ",original_opcode)
                                    instr_len = len(entry[0].new_instruction.bytes)
                                    
                                    new_bytes = original_opcode.to_bytes(original_op_len, byteorder='little') + offset.to_bytes(instr_len - original_op_len, byteorder='little', signed=True)
                                    bytes_arr = bytearray(new_bytes)
                                    new_length = len(bytes_arr)
                                    print("address: ",hex(entry[0].new_instruction.address))

                                    if instr_len != new_length:
                                        print("PII: instr_len != new_length")
                                        print(f"instr_len: {instr_len}, new_length: {new_length}")
                                        print("bytes_arr: ",bytes_arr)
                                        print("original_opcode: ",original_opcode)
                                        print("offset: ",offset)
                                        print("old_instr: ",entry[0].new_instruction.bytes)
                                        print("new_instr: ",bytes_arr)
                                    else:
                                        for x,i in enumerate(self.cs.disasm(bytes_arr,entry[0].new_instruction.address)):
                                            entry[0].new_instruction = i
                                            print(f"new_instr:{hex(i.address)}  {i.mnemonic} {i.op_str} ")
                                            do_not_touch_instr.append(entry[0].new_instruction)
                                            self.do_not_touch.append(entry[0].new_instruction)
                                        continue


                                diff = original_length - new_length
                                for _ in range(diff):
                                    bytes_arr.append(0x90)
                                
                                for x,i in enumerate(self.cs.disasm(bytes_arr,entry[0].new_instruction.address)):
                                    if x == 0:
                                        entry[0].new_instruction = i
                                    else:
                                        new_instr = Instruction(i,i,i,None,None)
                                        new_instr.address_history.append(i.address)
                                        self.insert_instruction(index+x,new_instr)
                                        inserted_instructions = True
                            # if the new size is bigger re-iterate this function
                            elif new_length > original_length:
                                re_iterate = True
                                diff = new_length - original_length

                                print("NEW_LEN > ORIG_LEN")
                                for i in self.cs.disasm(bytes_arr,entry[0].new_instruction.address):
                                    entry[0].new_instruction = i

                                new_str = f"{entry[0].new_instruction.mnemonic} {entry[1].new_instruction.address}"
                                new_asm, _ = self.ks.asm(new_str, entry[0].new_instruction.address)
                                new_bytes = bytearray(new_asm)
                                for x,i in enumerate(self.cs.disasm(new_bytes,entry[0].new_instruction.address)):
                                    entry[0].new_instruction = i

                        # if not different just patch the instruction
                        else:
                            for i in self.cs.disasm(bytes_arr,entry[0].new_instruction.address):
                                entry[0].new_instruction = i
                except Exception as e:
                    print("Errore in update_label_table(): ",e)
                    traceback.print_exc()

                    print("Indirizzo: ",hex(entry[0].new_instruction.address))
                    print("stringa: ",entry[0].new_instruction.mnemonic + '  ' + entry[0].new_instruction.op_str)
                    # print("Indirizzo jump: ",hex(jmp_addr))
                    print("bytes: ",entry[0].new_instruction.bytes)
                    print("\n\n\n")

                    continue


    def update_label_table_brain(self):
        print("UPDATE LABEL TABLE")

        # if during patching some JMP or CALL becomes bigger (example 3 byte --> 5 byte)
        #   i need to re iterate the all patching process
        re_iterate = True
        num_iterazioni = 0

        inserted_instructions = False
        while re_iterate == True:
            print("ITERANDO: num_iterazioni: ",num_iterazioni)
            # always update instructions beforse patching them, otherwise instructions addresses will be broken
            self.update_instr()
            re_iterate = False
            num_iterazioni += 1
            # try:

            # iterate the list of jmp/call instructions
            for entry in self.short_label_table:
                try:

                    # various checks 
                    if self.check_if_inside_jmp_table(entry[0].new_instruction.address) == True:
                        continue

                    if (x86_const.X86_GRP_JUMP not in entry[0].new_instruction.groups) and (x86_const.X86_GRP_CALL not in entry[0].new_instruction.groups) and (entry[0].new_instruction.mnemonic != 'loop'):
                        continue

                    if (entry[0].new_instruction.operands[0].type == x86_const.X86_OP_REG):
                        continue
                    # check if it is a jmp to far stuff (improbable), do not patch it here because it is patched in adjust_out_text_reference()
                    if 'ptr' in entry[0].new_instruction.op_str:
                        continue



                        # time.sleep(2)

                    # extract the jmp address from the string (yea i love python, so easy)
                    old_jump_address = zone_utils.estrai_valore(entry[0].new_instruction.op_str)


                    if old_jump_address == 0:
                        print(entry[0].new_instruction.mnemonic, entry[0].new_instruction.op_str)
                    


                    jmp_addr = zone_utils.estrai_valore(entry[0].new_instruction.op_str)
                    jmp_addr_ptr = entry[1].new_instruction.address
                    
                    index = self.instructions.index(entry[0])

                    # check if the jmp address is right
                    if jmp_addr != jmp_addr_ptr:
                        original_length = len(entry[0].new_instruction.bytes)

                        # assemblate with a string the new instruction
                        str_instr = f"{entry[0].new_instruction.mnemonic} {hex(jmp_addr_ptr)}"

                        bytes_arr = None
                        ################checko se ci sono istruzioni infami pezze di mmerda cacone ridicole#########
                        if (entry[0].new_instruction.mnemonic == 'jrcxz' or entry[0].new_instruction.mnemonic == 'loop'):

                            # bytes_arr = bytearray(asm(str_instr, arch='amd64'))
                            # bytes_arr = asm(str_instr, arch='x86_64')

                            print("JRCXZ/LOOP: \n")

                        ######################################################

                        if entry[0].new_instruction.mnemonic == 'jrcxz':
                            diff = abs(jmp_addr_ptr - entry[0].new_instruction.address)
                            print(f"###############\nDIFF: {diff}\n###############\n")
                            if diff > 120:
                                
                                print("\n###########################################\n")
                                print("DIFF > 120!!\n")
                                print(f"DIFF: {diff}\n")
                                print("PLEASE RESTART THE SOFTWARE UNTIL DIFF < 120\n")
                                print("EXITING...............\n")
                                print("###########################################\n")

                                # Restart with the *same* command line. The old
                                # version only passed sys.argv[0] and sys.argv[1],
                                # losing --extract-data, -eq, -o, etc.
                                try:
                                    restarts = int(os.environ.get(
                                        "POBF_JRCXZ_RESTARTS", "0"))
                                except ValueError:
                                    restarts = 0
                                if restarts >= 20:
                                    print("Too many restarts (jrcxz distance "
                                          "still > 120); aborting.")
                                    sys.exit(1)
                                env = os.environ.copy()
                                env["POBF_JRCXZ_RESTARTS"] = str(restarts + 1)
                                command = ([sys.executable,
                                            os.path.abspath(sys.argv[0])]
                                           + sys.argv[1:])
                                print("RESTARTING:",
                                      subprocess.list2cmdline(command))
                                result = subprocess.run(command, env=env)
                                sys.exit(result.returncode)
                                # start()
                                
                            #     time.sleep(2)
                            #     exit(0)
                            # time.sleep(2)
                        asm, _ = self.ks.asm(str_instr, entry[0].new_instruction.address)
                        bytes_arr = bytearray(asm)

                        new_length = len(bytes_arr)
                        # check if the new assembled instruction is different in size from the old one
                        if original_length != new_length:
                            # if the new size is lower just insert NOPs to pad
                            if original_length > new_length:
                                diff = original_length - new_length
                                for _ in range(diff):
                                    bytes_arr.append(0x90)
                                
                                for x,i in enumerate(self.cs.disasm(bytes_arr,entry[0].new_instruction.address)):
                                    if x == 0:
                                        entry[0].new_instruction = i
                                    else:
                                        new_instr = Instruction(i,i,i,None,None)
                                        new_instr.address_history.append(i.address)
                                        self.insert_instruction(index+x,new_instr)
                                        inserted_instructions = True
                            # if the new size is bigger re-iterate this function
                            elif new_length > original_length:
                                re_iterate = True
                                diff = new_length - original_length

                                print("NEW_LEN > ORIG_LEN")
                                for i in self.cs.disasm(bytes_arr,entry[0].new_instruction.address):
                                    entry[0].new_instruction = i

                                new_str = f"{entry[0].new_instruction.mnemonic} {entry[1].new_instruction.address}"
                                new_asm, _ = self.ks.asm(new_str, entry[0].new_instruction.address)
                                new_bytes = bytearray(new_asm)
                                for x,i in enumerate(self.cs.disasm(new_bytes,entry[0].new_instruction.address)):
                                    entry[0].new_instruction = i

                        # if not different just patch the instruction
                        else:
                            for i in self.cs.disasm(bytes_arr,entry[0].new_instruction.address):
                                entry[0].new_instruction = i
                except Exception as e:
                    print("Errore in update_label_table(): ",e)
                    traceback.print_exc()

                    print("Indirizzo: ",hex(entry[0].new_instruction.address))
                    print("stringa: ",entry[0].new_instruction.mnemonic + '  ' + entry[0].new_instruction.op_str)
                    # print("Indirizzo jump: ",hex(jmp_addr))
                    print("bytes: ",entry[0].new_instruction.bytes)
                    print("\n\n\n")

                    continue

    # this also is some serious fucked up stuff
    # this function patched all the jmp/call/mov or all the instructions which have references to some very far addresses
    # these instructions all have this structure:   INSR  OP1, QWORD/DWORD PTR [REG + 0xNUM],
    # i will only patch the instructions with REG = RIP
    def adjust_out_text_references(self):
        # same as before, if instructions become bigger i have to re-iterate
        re_iterate = True
        inserted_instructions = False
        while re_iterate == True:
            re_iterate = False
            self.update_instr()
            for num_instr,instr in enumerate(self.instructions):
                inside_jmp_table = self.check_if_inside_jmp_table(instr.original_instruction.address)
                if inside_jmp_table == True:
                    continue


                if instr is not None:
                    # 
                    if ('rip +' in instr.new_instruction.op_str):

                        # extract the offset
                        valore_originale = zone_utils.estrai_valore(instr.original_instruction.op_str)
                        if valore_originale == 0:
                            continue
                        if num_instr == len(self.instructions) - 1:
                            continue

                        # calculate the address that is pointing (RIP + offset)
                        addr = self.instructions[num_instr + 1].original_instruction.address + valore_originale


                        #checko se l'indirizzo e'all'interno della .text
                        #  check if the address is inside the .text 
                        # MAYBE THIS CHECK IS WRONG, I SHOULD PATCH ALSO IF IT IS INSIDE .TEXT
                        # if addr > self.base_address and addr < self.base_address + self.code_section_size:
                        #     for i in self.instructions:
                        #         if i.original_instruction.address == addr:
                        #             addr = i.new_instruction.address
                        #             print("NUOVO INDIRIZZO JUMP RIP+ : ",hex(addr))
                        #             break
            
                        # calculate the new offset i need to insert in the instruction
                        offset = addr - self.instructions[num_instr + 1].new_instruction.address

                        old_string = instr.new_instruction.mnemonic + ' ' + instr.new_instruction.op_str

                        # rimpiazzo il nuovo offset con il vecchio offset nella stringa e assemblo
                        # replace the new offset with the old offset in the string and assemble
                        new_string = old_string.replace(hex(valore_originale),hex(offset))



                        try:
                            asm, _ = self.ks.asm(new_string, instr.new_instruction.address)
                            asm = bytearray(asm)
                        except:
                            nuovi_bytes = offset.to_bytes(4, byteorder='little')
                            bytes_vecchi = valore_originale.to_bytes(4, byteorder='little')
                            asm = bytearray(instr.new_instruction.bytes.replace(bytes_vecchi,nuovi_bytes))
                            print('vecchi bytes: ',instr.new_instruction.bytes)
                            print('nuovi bytes: ',asm)


                        # always check if the new instruction is bigger than the old one
                        if(len(asm) < len(instr.new_instruction.bytes)):
                            
                            # this check is caused by the fact that keystone does not assemble the 0x48 byte very often, it is something about x64 arch. i do not remember
                            if(instr.new_instruction.bytes[0] == 0x48 and (len(instr.new_instruction.bytes) - len(asm) == 1)):


                                asm.insert(0,0x48)
                                for i in self.cs.disasm(asm, instr.new_instruction.address):
                                    instr.new_instruction = i
                            else:                     
                                ##########DA IMPLEMENTARE################
                                nop_num = instr.new_instruction.size - len(asm)
                                for i in range(nop_num):
                                    asm.append(0x90)
                                for x,i in enumerate(self.cs.disasm(asm, instr.new_instruction.address)):
                                    if x == 0:
                                        instr.new_instruction = i
                                    else:
                                        insr = Instruction(i,i,i,None,None)
                                        insr.address_history.append(i.address)
                                        self.insert_instruction(num_instr + x, insr)
                                        inserted_instructions = True
                        elif len(asm) == len(instr.new_instruction.bytes):
                            for i in self.cs.disasm(asm, instr.new_instruction.address):
                                instr.new_instruction = i
                        else:
                            print(f"{hex(instr.new_instruction.address)} SOSPETTO: len(asm) > instr2.new_instruction.size in out_refs rip+")
                            re_iterate = True

                    # same stuff but for jump at addressess before
                    elif ('rip -' in instr.new_instruction.op_str):
                        #print(hex(instr.original_instruction.address),instr.original_instruction.mnemonic,instr.original_instruction.op_str)
                        valore_originale = zone_utils.estrai_valore(instr.original_instruction.op_str)
                        # print("valore_originale: ",valore_originale)
                        if valore_originale == 0:
                            continue
                        addr = self.instructions[num_instr + 1].original_instruction.address - valore_originale

                        #checko se l'indirizzo e'all'interno della .text
                        if addr > self.base_address and addr < self.base_address + self.code_section_size:
                            for i in self.instructions:
                                if i.original_instruction.address == addr:
                                    addr = i.new_instruction.address
                                    break

                        offset = self.instructions[num_instr + 1].new_instruction.address - addr

                        #print(f"valore vecchio: {hex(valore_originale)}, addr nuovo: {hex(new_addr)}")
                        old_string = instr.new_instruction.mnemonic + ' ' + instr.new_instruction.op_str

                        new_string = old_string.replace(hex(valore_originale),hex(offset))

                        asm, _ = self.ks.asm(new_string, instr.new_instruction.address)
                        asm = bytearray(asm)

                        if(len(asm) < len(instr.new_instruction.bytes)):
                            #checka il problema del bytes 0x48 che ks non lo assembla molto spesso
                            if(instr.new_instruction.bytes[0] == 0x48 and (len(instr.new_instruction.bytes) - len(asm) == 1)):
                                # print("cosa strana")
                                # print("Indirizzo: ",hex(instr.new_instruction.address))

                                asm.insert(0,0x48)
                                for i in self.cs.disasm(asm, instr.new_instruction.address):
                                    instr.new_instruction = i
                            else:                     
                                ##########DA IMPLEMENTARE################
                                # print("Indirizzo: ",hex(instr.new_instruction.address))
                                # print('nuova lunghezza asm: ',len(asm))
                                # print('vecchia lunghezza instr.new_instruction: ',instr.new_instruction.size)
                                nop_num = instr.new_instruction.size - len(asm)
                                for i in range(nop_num):
                                    asm.append(0x90)
                                for x,i in enumerate(self.cs.disasm(asm, instr.new_instruction.address)):
                                    if x == 0:
                                        instr.new_instruction = i
                                    else:
                                        insr = Instruction(i,i,i,None,None)
                                        insr.address_history.append(i.address)
                                        self.insert_instruction(num_instr + x, insr)
                                        inserted_instructions = True
                        elif len(asm) == len(instr.new_instruction.bytes):
                            for i in self.cs.disasm(asm, instr.new_instruction.address):
                                instr.new_instruction = i
                        else:
                            print(f"{hex(instr.new_instruction.address)} SOSPETTO: len(asm) > instr2.new_instruction.size in out_refs rip-")
                            re_iterate = True
                else:
                    print("dentro adjust_out_text_references(), instr e' None")


    # a simple function that given the original address will return the new address
    def locate_by_address(self, address):
        instr = self.instr_dict[address]            
        if instr.original_instruction.address == address:
            return instr
        return None

    #  a function that will patch the RELOC_TABLE of the PE file
    # https://0xrick.github.io/win-internals/pe7/ read this to understand why we need to patch the reloc table
    def adjust_reloc_table(self):
        # iterate every table
        for entries in self.pe.DIRECTORY_ENTRY_BASERELOC:
            # iterate evry entry (every address to reloc)
            for reloc in entries.entries:
                data = self.pe.get_qword_at_rva(reloc.rva)
                # print("data: ",hex(data))

                data = data - self.pe.OPTIONAL_HEADER.ImageBase


                if data not in self.instr_dict:
                    continue

                if self.instr_dict[data] is not None:
                    # print("RELOC: ",hex(reloc.rva))
                    instr = self.instr_dict[data]

                    self.pe.set_qword_at_rva(reloc.rva, instr.new_instruction.address + self.pe.OPTIONAL_HEADER.ImageBase)

        self.pe.write(self.file)

    # a function that given an index and an instruction will insert the new instruction in self.instructions
    def insert_instruction(self,index,instruction):
        instruction_number = len(self.instructions)
        if index >= instruction_number:
            self.instructions.append(instruction)
            return
        self.instructions[index - 1].next_instruction = instruction
        self.instructions[index].prev_instruction = instruction

        instruction.prev_instruction = self.instructions[index - 1]
        instruction.next_instruction = self.instructions[index]

        self.instructions.insert(index,instruction)

    def eliminate_instruction(self, index):
        self.instructions[index - 1].next_instruction = self.instructions[index + 1]
        self.instructions[index + 1].prev_instruction = self.instructions[index - 1]
        self.instructions.pop(index)
                

    # function that randomly inserts some do-nothing operations
    def insert_random_nop(self):

        inserted_nops = 0
        for num_instr,instr in enumerate(self.instructions):
            if id(instr) in self.data_instruction_ids:
                continue
            if id(instr) in self.nop_skip_ids:
                continue
            if (instr.next_instruction is not None
                    and id(instr.next_instruction) in self.data_instruction_ids):
                # do not insert between a call and its inline getpc data
                continue
            if instr.new_instruction.address < getattr(self, "nop_min_address", 0):
                # only modify code after the last inline data block
                continue
            if num_instr == 0:
                continue
            try:

                # if instr.new_instruction.address >= new_entry_point:
                #     break
                if instr.new_instruction.mnemonic == '.byte' or instr.new_instruction.mnemonic == 'nop':
                    continue
                #checko che non sia dentro una jmp table della .text
                if self.check_if_inside_jmp_table(instr.original_instruction.address) == True:
                    continue

                if instr.prev_instruction is not None and instr.prev_instruction.new_instruction.mnemonic == 'pushfd' or instr.new_instruction.mnemonic == 'pushfd':
                    continue


                # le nop sono:  NOP, 
                #               XCHG REG,REG,   ----> PER ORA NON FUNZIONA
                #               SUB REG,0x0,    ----> FUNZIONA
                #               ADD REG,0x0,    ----> messa
                #               MOV REG, REG, 
                #               LEA REG, [REG+0],
                #               PUSH REG ----------- POP REG  ---> funziona (ESEGUIRE SOLO 1 volta, nop_num = 1)
                #               OR REG, REG
                #               XOR REG, 0x0
                #               AND REG, REG
                #               INC REG ----------- DEC REG
                #               DEC REG ----------- INC REG
                #               SAR REG, 0x0
                #               SHR REG, 0x0
                #               SHL REG, 0x0
                #               RCL REG, 0x0
                #               RCR REG, 0x0 
                asm = None
                operazione = None
                reg_list = self.reg_list32
                reg = None

                # just a random probability to insert a nop
                probability = random.randint(0,100)
                if probability <= 100:

                    # choose a random NOP operation
                    operazione = 'nop'
                    # choose a random number of NOPs to insert
                    nop_num = random.randint(1,2)

                    # choose a random register to do the nop
                    reg = random.choice(reg_list)

# IMPORTANT : Why there is pushfd; nop; popfd in every instruction?
# BECAUSE even if these operations do nothing they still fuck up the CPU flags, therefore you need to save them and restore
# maybe this is bad solution because it can be easily signatured (?) 

                    if operazione == 'nop':
                        asm = b'\x90' * random.randint(1, 4)

                    if operazione == 'sub':
                        asm, _ = self.ks.asm(f'pushfd;sub {reg},0x0; popfd', instr.new_instruction.address + instr.new_instruction.size)
                    
                    if operazione == 'add':
                        asm, _ = self.ks.asm(f'pushfd;add {reg},0x0; popfd', instr.new_instruction.address + instr.new_instruction.size)
                    
                    if operazione == 'mov':
                        asm, _ = self.ks.asm(f'pushfd;mov {reg},{reg}; popfd', instr.new_instruction.address + instr.new_instruction.size)

                    if operazione == 'lea':
                        asm, _ = self.ks.asm(f'pushfd;lea {reg},[{reg}+0]; popfd', instr.new_instruction.address + instr.new_instruction.size)

                    if operazione == 'inc':
                        nop_num = 1
                        asm, _ = self.ks.asm(f'pushfd;dec {reg}; inc {reg}; popfd', instr.new_instruction.address + instr.new_instruction.size)
                    
                    if operazione == 'sar':
                        asm, _ = self.ks.asm(f'pushfd;sar {reg},0x0; popfd', instr.new_instruction.address + instr.new_instruction.size)
                    
                    if operazione == 'shr':
                        asm, _ = self.ks.asm(f'pushfd;shr {reg},0x0; popfd', instr.new_instruction.address + instr.new_instruction.size)
                    
                    if operazione == 'shl':
                        asm, _ = self.ks.asm(f'pushfd;shl {reg},0x0; popfd', instr.new_instruction.address + instr.new_instruction.size)
                    
                    if operazione == 'rcl':
                        asm, _ = self.ks.asm(f'pushfd;rcl {reg},0x0; popfd', instr.new_instruction.address + instr.new_instruction.size)
                    
                    if operazione == 'rcr':
                        asm, _ = self.ks.asm(f'pushfd;rcr {reg},0x0; popfd', instr.new_instruction.address + instr.new_instruction.size)
                    
                    if operazione == 'xor':
                        asm, _ = self.ks.asm(f'pushfd;xor {reg},0x0; popfd', instr.new_instruction.address + instr.new_instruction.size)

                    if operazione == 'and':
                        asm, _ = self.ks.asm(f'pushfd;and {reg},{reg}; popfd', instr.new_instruction.address + instr.new_instruction.size)

                    
                    if operazione == 'or':
                        asm, _ = self.ks.asm(f'pushfd;or {reg},{reg}; popfd', instr.new_instruction.address + instr.new_instruction.size)
                    
                    if operazione == 'jmp':
                        # stupid jmp to next instruction
                        asm = bytearray([0xEB,0x00])

                        asm = bytearray(b'f\x9c') + asm + bytearray(b'f\x9d')
                        asm = bytearray([0x90])

                    # asm = bytearray([0x90])
                    asm = bytearray(asm)
                    for x,i in enumerate(self.cs.disasm(asm, instr.new_instruction.address + instr.new_instruction.size )):
                        insr = Instruction(i,i,i,None,None)
                        insr.address_history.append(i.address)

                        self.insert_instruction(num_instr + 1 + x, insr)
                    inserted_nops += 1

                self.nops_addedd = inserted_nops
            except Exception as e:
                print("Errore in insert_random_nop(): ",e)
                print("NUM_INSTR ERRORE: ",num_instr)
                traceback.print_exc()

                continue

    def chaos_cf(self):

        #1) dividi il codice in blocchi di istruzioni di grandezza casuale tra 5 e 12
        #2) alla fine di ogni blocco inserisci un jmp al blocco successivo
        # shuffla i blocchi

        single_block = []
        self.block_size = random.randint(5,9)
        # self.block_size = 7
        print("BLOCK LENGTH: ",self.block_size)


        

        skip = False
        for num_instr,instr in enumerate(self.instructions):

            tmp_instr = instr
            
            last_block_instr = False

            if skip == True:
                skip = False
                continue
            if (num_instr == len(self.instructions) - 1):
                break
            if (num_instr + 2) % self.block_size == 0 and num_instr != 0:
                
                # inserisco un jmp al blocco successivo
                single_block.append(tmp_instr)
                address = instr.new_instruction.address + instr.new_instruction.size + 2

                asm, _ = self.ks.asm(f'jmp {address}', instr.new_instruction.address + instr.new_instruction.size)
                # asm = bytearray(b'\xeb\x00')
                asm = bytearray(asm)
                for i in self.cs.disasm(asm, instr.new_instruction.address + instr.new_instruction.size):

                    new_jmp = Instruction(i,i,i,instr.new_instruction,instr.next_instruction)

                    

                    #inserisci istruzione nella lista
                    self.insert_instruction(num_instr +1,new_jmp)
                    #aggiungi alla label table
                    self.short_label_table.append((new_jmp,new_jmp.next_instruction))


                    tmp_instr = new_jmp
                    skip = True

                last_block_instr = True
            
            
            single_block.append(tmp_instr)

            if last_block_instr == True:
                self.instr_blocks.append(single_block)
                single_block = []

        # shuffla i blocchi ma non il primo

    def shuffle_blocks(self):



        blocco_jrcxz = 99999999999
        blocco_jrcxz_jmp = 999999999999

        jmp_addr = None

        block_distance = -1


        
        
        blocks = self.instr_blocks[1:]

        # while  block_distance > 4 and block_distance < 0:
        random.shuffle(blocks)



        self.instr_blocks = [self.instr_blocks[0]] + blocks


        new_instructions = []
        for block in self.instr_blocks:
            for instr in block:
                new_instructions.append(instr)

        self.instructions = new_instructions

        for x,instr in enumerate(self.instructions):
            if x == 0:
                instr.next_instruction = self.instructions[x+1]

            elif x == len(self.instructions) - 1:
                instr.prev_instruction = self.instructions[x-1]

            else:
                instr.prev_instruction = self.instructions[x-1]
                instr.next_instruction = self.instructions[x+1]

        # diff = 99999
        # for entry in self.short_label_table:
        #     if entry[0].new_instruction.mnemonic == "jrcxz":
        #         jmp_addr_ptr = entry[1].new_instruction.address
        #         diff = abs(jmp_addr_ptr - entry[0].new_instruction.address)
        #         print(f"\n################DIFF in shuffle_blocks(): {diff}\n")

        # if diff > 120:
        #     print("diff > 120\n")
        #     print("reiterating shuffle_blocks....")
        #     self.shuffle_blocks()


    def check_jcrxz_ok(self):
        check = False
        for entry in self.short_label_table:
            jmp_addr_ptr = entry[1].new_instruction.address
            diff = abs(jmp_addr_ptr - entry[0].new_instruction.address)
            print("DIFF: ",diff)
            if diff > 120:
                return False
        return True

    # a function that will print the blocks to a file
    def print_blocks(self):
        with open('blocks.txt', 'r+') as f:
            for n,block in enumerate(self.instr_blocks):
                f.write("###############################\n")
                for instr in block:
                    
                    stringa = f"{n} :  {hex(instr.new_instruction.address)} {instr.new_instruction.mnemonic} {instr.new_instruction.op_str}\n"
                    f.write(stringa)




    # function that will write modifications to the PE file
    def write_pe_file(self):
        new_bytes = b''
        for i in self.instructions:
            new_bytes += i.new_instruction.bytes
        
        length = self.original_code_length

        new_bytes = new_bytes[:length]
        # gap = self.pe.OPTIONAL_HEADER.SectionAlignment - (len(new_bytes) % self.pe.OPTIONAL_HEADER.SectionAlignment)

        # gap_bytes = (bytearray([0 for _ in range(gap)]))
        # new_bytes += gap_bytes
        new_entry_point = self.locate_by_address(self.original_entry_point).new_instruction.address
        

        #indirizzo dove viene salvato l'entry point
        entry_point_addr = self.pe.DOS_HEADER.e_lfanew + 0x28
        
        with open(self.file, "r+b") as f:

            original_file = bytearray(f.read())
            print(f"LEN ORIGINAL_FILE: {len(original_file)}")
            new_bytes = bytearray(new_bytes)

            #riscrivo la .text
            original_file[self.code_raw_start : self.code_raw_start + len(new_bytes)] = new_bytes
            #scrivo l' entry point
            original_file[entry_point_addr: entry_point_addr + 4] = new_entry_point.to_bytes(4, byteorder='little')
            print(f"LEN NUOVO_FILE: {len(original_file)}")

            f.seek(0)
            f.write(original_file)       
        




    def update_old_instructions(self,instr):
        instr.old_instruction = instr.new_instruction

    # function that converts raw addressess to relative addresses
    def convert_raw_to_rva(self,raw_address,section):
        return raw_address + section.VirtualAddress - section.PointerToRawData
    
    def eliminate_loop_instructions(self):
        restart = True
        try:
            while restart == True:
                restart = False
                for x,instr in enumerate(self.instructions):
                    if instr.new_instruction.mnemonic == 'loop':
                        print("TROVATO LOOP")
                        addr = zone_utils.estrai_valore(instr.new_instruction.op_str)

                        self.eliminate_instruction(x)
                        
                        stringa = f"dec ecx;jne {hex(addr)}"
                        asm, _ = self.ks.asm(stringa, instr.new_instruction.address)
                        bytes_arr = bytearray(asm)
                        for n,i in enumerate(self.cs.disasm(bytes_arr,instr.new_instruction.address)):
                            new_instr = Instruction(i,i,i,None,None)
                            self.insert_instruction(x+n,new_instr)
                            if i.mnemonic == 'jne':
                                self.short_label_table.append((new_instr,self.instr_dict[addr]))
                        restart = True
                        # break
        except Exception as e:
            print("Errore in eliminate_loop_instructions(): ",e)
            traceback.print_exc()
    
    def eliminate_jrcxz_instructions(self):
        restart = True

        while restart == True:
            restart = False
            for x,instr in enumerate(self.instructions):
                if instr.new_instruction.mnemonic == 'jrcxz':
                    print("TROVATO LOOP")
                    addr = zone_utils.estrai_valore(instr.new_instruction.op_str)

                    self.eliminate_instruction(x)
                    
                    stringa = f"dec rcx;jne {hex(addr)}"
                    asm, _ = self.ks.asm(stringa, instr.new_instruction.address)
                    bytes_arr = bytearray(asm)
                    for n,i in enumerate(self.cs.disasm(bytes_arr,instr.new_instruction.address)):
                        new_instr = Instruction(i,i,i,None,None)
                        self.insert_instruction(x+n,new_instr)
                        if i.mnemonic == 'jne':
                            self.short_label_table.append((new_instr,self.instr_dict[addr]))
                    restart = True
                    # break


    # function that checks if an instruction(given its address) is inside a jump table
    def check_if_inside_jmp_table(self,address):
        inside_jmp_table = False
        for jmp in self.start_end_table:
            if address >= jmp[0] and address <= jmp[1]:
                inside_jmp_table = True

        return inside_jmp_table

    # function that creates a jump table
    # here i found the solution https://blog.es3n1n.eu/posts/obfuscator-pt-1/
    def create_jmp_table(self):
        print("CREO JUMP TABLE")
        for instr in self.instructions:
            if instr.old_instruction.id == x86_const.X86_INS_JMP and instr.old_instruction.operands[0].type == x86_const.X86_OP_REG:
                if instr.prev_instruction.new_instruction.mnemonic == 'add' and instr.prev_instruction.prev_instruction.new_instruction.mnemonic == 'mov':
                    indirizzo_jmp_table = zone_utils.estrai_valore(instr.prev_instruction.prev_instruction.new_instruction.op_str)
                    self.jump_table.append(indirizzo_jmp_table)

        self.jump_table.sort()

        for n,i in enumerate(self.jump_table):
            start = i
            end = 0
            x = 0
            if n != len(self.jump_table) - 1:
                while (i + x*4 < self.jump_table[n+1]):
                    addr = self.pe.get_dword_at_rva(i + x*4)
                    is_an_instruction = False
                    for instr in self.instructions:
                        if instr.original_instruction.address == addr:
                            is_an_instruction = True
                            break
                    if is_an_instruction == False:
                        break
                    x += 1           
                end = i + x*4 
            self.start_end_table.append((start,end))
        with open('jump_table.txt', 'r+') as f:
            for entry in self.start_end_table:
                stringa = f"{hex(entry[0])} {hex(entry[1])}\n"
                f.write(stringa)

    # function that patches the jump table
    def adjust_jmp_table(self):

        for n,i in enumerate(self.jump_table):
            x = 0
            if n != len(self.jump_table) - 1:
                while (i + x*4 < self.jump_table[n+1]):
                    addr = self.pe.get_dword_at_rva(i + x*4)
                    is_an_instruction = False
                    for instr in self.instructions:
                        if instr.original_instruction.address == addr:
                            self.pe.set_dword_at_rva(i + x*4, instr.new_instruction.address)
                            is_an_instruction = True
                            break
                    if is_an_instruction == False:
                        break
                    x += 1

        self.pe.write(self.file)

    # another technique that consists of:
    # 1) randomically shuffling every instruction
    # 2) a map that holds the new address and the chronologically ordered instructions
    # 3) A stub that jumps manually to every instruction executing in the correct order
    def check_unused_registers(self):
        unused_regs = []
        for reg in self.reg_list32:
            unused_regs.append(reg)
        
        for instr in self.instructions:
            instr_str = f"{instr.new_instruction.mnemonic} {instr.new_instruction.op_str}"
            for reg in self.reg_list32:
                if reg in instr_str:
                    if reg in unused_regs:
                        unused_regs.remove(reg)
        print("UNUSED REGISTERS: ",unused_regs)

        if len(unused_regs) == 0:
            print("NO UNUSED REGISTERS, using ebp")
            unused_regs.append('ebp')
        return unused_regs
    def estimate_stub_address(self):
        original_size = 0
        instruction_num = 0
        for instr in self.instructions:
            original_size += len(instr.new_instruction.bytes)
            instruction_num += 1

        probable_addr = original_size + (1 + 4 + 5 + 5) * instruction_num    
        probable_addr = probable_addr + (100 - (probable_addr % 100)) + 0x100

        print("EStimated stub address: ",probable_addr)
        return probable_addr
        
    def brain_adjust(self):
        self.stub_address = self.estimate_stub_address()


        bytes_added = 0

        re_iterate = True
        actual_index = 0
        counter = 0
        while re_iterate == True:
            try:
                re_iterate = False
                for x,instr in enumerate(self.instructions):
                    if x < actual_index:
                        continue
                    
                    if x == 0:
                        actual_index += 1
                        continue
                    
                    if instr.new_instruction.mnemonic == 'jrcxz':
                        asm1 = "pop eax"
                        asm1, _ = self.ks.asm(asm1,instr.new_instruction.address + bytes_added)
                        asm1 = bytearray(asm1)

                        asm2 = bytearray(instr.new_instruction.bytes)
                        asm3 = f"push {hex(0x3e8 + actual_index)}"

                        asm3, _ = self.ks.asm(asm3,instr.new_instruction.address + bytes_added)

                        asm4 = f"jmp {hex(self.stub_address)}"
                        asm4, _ = self.ks.asm(asm4,instr.new_instruction.address + bytes_added)
                        asm4 = bytearray(asm4)
                        continue
                    original_length = len(instr.new_instruction.bytes)
                    new_str = f"pop eax;lea esp, [esp + 4];{instr.new_instruction.mnemonic} {instr.new_instruction.op_str};push {hex(0x3e8 + counter)};jmp {hex(self.stub_address)}"
                    
                    asm, _ = self.ks.asm(new_str,instr.new_instruction.address + bytes_added)
                    asm = bytearray(asm)
                    counter += 1

                    for x2,i in enumerate(self.cs.disasm(asm,instr.new_instruction.address + bytes_added)):
                        re_iterate = True
                        if x2 == 2:
                            actual_index += 1
                            continue
                            
                        new_instr = Instruction(i,i,i,None,None)
                        self.insert_instruction(x+x2, new_instr)
                        actual_index += 1
                    bytes_added += (len(asm) - original_length)
                    break
            except Exception as e:
                print("Errore in brain_adjust(): ",e)
                print("new_str: ",new_str)
                traceback.print_exc()
                re_iterate = False
                continue
        payload_size = 0
        for instr in self.instructions:
            payload_size += len(instr.new_instruction.bytes)
        print("OBFUSCATED PAYLOAD SIZE: ",payload_size)

        self.payload_size = payload_size
    def re_adjust_brain(self):
        for x,instr in enumerate(self.instructions):
            if instr.new_instruction.address >= self.stub_address:
                return
            if x % self.wrap_instruction_num != 0:
                continue
            elif instr.new_instruction.mnemonic == 'nop':
                continue
            elif instr.new_instruction.mnemonic == 'jmp':
                new_str = f"{instr.new_instruction.mnemonic} {self.stub_address}"
                asm, _ = self.ks.asm(new_str,instr.new_instruction.address)
                asm = bytearray(asm)
                for i in self.cs.disasm(asm,instr.new_instruction.address):
                    instr.new_instruction = i
            else:
                print("Errore strano, non tornano i conti non c'e' una JMP ogni tre istruzioni")
    def estimate_stub_size(self):
        stub_str = f'''
        push eax;
        push ecx;
        mov ecx, [esp + 0x8]
        pushfd;
        sub ecx, 0x3e8;
        inc ecx;

        call 0x1000
        pop eax;

        mov eax, [eax + 0x40];
        mov ecx, [eax + {self.mem_address} - 5 + ecx * 4];
        sub ecx, 0x5
        add eax, ecx
        popfd;
        pop ecx;
        jmp eax;
        '''

        asm, _ = self.ks.asm(stub_str,self.stub_address)
        bytes_arr = bytearray(asm)
        return len(bytes_arr)     

    def estimate_stub2_size(self):
        stub2_str = f'''
        pop ebp;
        mov [ebp - 5 + 0x1000], ebp;
        push ebp;
        jmp ebp;
        '''
        asm, _ = self.ks.asm(stub2_str,self.stub_address)
        bytes_arr = bytearray(asm)
        return len(bytes_arr)

    def shuffle_brain_blocks(self):
        counter = 0

        blocks = []
        block = []

        for x,instr in enumerate(self.instructions):
            if instr.new_instruction.mnemonic == 'pop' and instr.new_instruction.op_str == 'eax':
                if instr.next_instruction.new_instruction.mnemonic == "lea":
                    block.append(instr)
                    continue
            if x == len(self.instructions) - 1:
                block.append(instr)
                blocks.append(block)
                block = []
                continue
            if instr.new_instruction.mnemonic == 'jmp' and instr.next_instruction.new_instruction.mnemonic == 'pop' and instr.next_instruction.new_instruction.op_str == 'eax':
                block.append(instr)
                blocks.append(block)
                block = []
                continue
            block.append(instr)

        firstBlock = blocks[0]
        blocks = blocks[1:]

        random.shuffle(blocks)
        blocks = [firstBlock] + blocks

        new_instructions = []
        for block in blocks:
            for instr in block:
                new_instructions.append(instr)

        self.instructions = new_instructions       

        for x,instr in enumerate(self.instructions):
            if x == 0:
                instr.next_instruction = self.instructions[x+1]

            elif x == len(self.instructions) - 1:
                instr.prev_instruction = self.instructions[x-1]

            else:
                instr.prev_instruction = self.instructions[x-1]
                instr.next_instruction = self.instructions[x+1]

    def _pii_single_insn_32(self, text, address=0):
        try:
            asm, _ = self.ks.asm(text, address)
        except Exception as exc:
            print(f"[pii32] cannot assemble {text!r} at {address:#x}: {exc}")
            raise
        for capstone_instr in self.cs.disasm(bytes(asm), address):
            instr = Instruction(capstone_instr, capstone_instr,
                                capstone_instr, None, None)
            instr.address_history.append(capstone_instr.address)
            return instr
        return None

    def _pii_scratch_register_32(self, instructions):
        used = " ".join(
            f"{instr.new_instruction.mnemonic} {instr.new_instruction.op_str}"
            for instr in instructions)
        for reg in self.reg_list32:
            if reg in ("esp", "ebp"):
                continue
            if reg not in used:
                return reg
        print("WARNING: no unused PII scratch register; using ebx")
        return "ebx"

    def _pii_stub_text_32(self, map_displacement):
        # 32-bit indexed dispatcher with pushad/popad: all general registers
        # and flags are preserved. The target is parked in the saved-flags
        # slot, then popfd restores flags and ret jumps to the target.
        return ("pushad; "
                "mov esi, [esp + 32]; sub esi, 0x3e8; "
                "call 0; pop eax; "
                f"add eax, {map_displacement}; "
                "mov edx, [eax + esi * 4]; add eax, edx; "
                "mov ebx, eax; "
                "mov eax, [esp + 36]; mov [esp + 32], eax; "
                "mov [esp + 36], ebx; "
                "popad; popfd; ret")

    def _pii_stub_insns_32(self, map_displacement, address):
        # Assemble with a fixed 32-bit placeholder so `add eax, disp` always
        # uses the imm32 encoding. With a small displacement keystone picks
        # the shorter imm8 form, and the stub would change size between the
        # first layout guess and the final one, shifting the instruction map.
        sentinel = 0x11111111
        asm, _ = self.ks.asm(self._pii_stub_text_32(sentinel), address)
        asm = bytearray(asm)
        marker = sentinel.to_bytes(4, "little")
        position = asm.find(marker)
        if position < 0:
            raise RuntimeError("PII32 stub: displacement placeholder not found")
        asm[position:position + 4] = \
            (map_displacement & 0xFFFFFFFF).to_bytes(4, "little")
        for insn in self.cs.disasm(bytes(asm), address):
            if insn.mnemonic == "call":
                offset = insn.address - address
                asm[offset + 1:offset + 5] = b"\x00\x00\x00\x00"
                break
        return list(self.cs.disasm(bytes(asm), address))

    def _pii_call_next_32(self):
        for capstone_instr in self.cs.disasm(b"\xE8\x00\x00\x00\x00", 0):
            instr = Instruction(capstone_instr, capstone_instr,
                                capstone_instr, None, None)
            instr.address_history.append(capstone_instr.address)
            return instr
        return None

    # ------------------------------------------------------------------
    # Data layer (same interface as pobf.py)
    #
    # The symbolic analyzer is arch-parametric; what differs in 32-bit mode
    # is the reference classification (absolute 32-bit immediates, no
    # RIP-relative operands) and the getpc rewrite: there is no
    # `lea reg, [rip + disp]`, so the call is replaced by a jmp to a 5-byte
    # stub placed just before the moved data. The stub calls the original
    # consumer (the pop), so the pushed return address is the new data
    # address and the payload stays position-independent.
    # ------------------------------------------------------------------

    DATA_CACHE_SCHEMA = 1

    def _lea_reg_disp32(self, reg, displacement, address=0):
        """Assemble ``lea reg, [reg + disp32]`` with a fixed encoding.

        The displacement is patched in place so the instruction keeps the
        disp32 form (and therefore its size) for every value.
        """
        sentinel = 0x11111111
        asm, _ = self.ks.asm(f"lea {reg}, [{reg} + {sentinel}]", address)
        raw = bytearray(asm)
        if not raw:
            raise RuntimeError(f"cannot assemble lea {reg}, [{reg} + disp]")
        marker = sentinel.to_bytes(4, "little")
        position = raw.find(marker)
        if position < 0:
            raise RuntimeError("lea disp32 placeholder not found")
        raw[position:position + 4] = \
            (displacement & 0xFFFFFFFF).to_bytes(4, "little")
        return bytes(raw)

    def decode_original_at(self, address):
        """Decode one instruction from the current payload bytes at address."""
        code_base = 0
        if self.instructions:
            code_base = self.instructions[0].original_instruction.address
        offset = address - code_base
        if offset < 0 or offset >= len(self.raw_code):
            return None
        chunk = self.raw_code[offset:offset + 15]
        return next(self.cs.disasm(chunk, address, count=1), None)

    def _simulate_getpc_consumer(self, callee_address, max_steps=24):
        """Find the ``pop`` that consumes the return address pushed by a call.

        The classic getpc is ``call $+5; pop reg``. Some 32-bit stagers use a
        late pop instead: the callee starts with normal code, pushes/pops a
        few temporary values, and only then consumes the saved return
        address. This helper starts with one 4-byte item on the stack and
        walks instructions until a ``pop`` consumes it. Branches, calls,
        returns and unknown esp changes abort the simulation.
        """
        depth = 1  # the call pushed one 4-byte return address
        address = callee_address
        for _ in range(max_steps):
            insn = self.decode_original_at(address)
            if insn is None:
                return None
            mnemonic = insn.mnemonic
            ops = insn.operands

            if mnemonic.startswith("push"):
                depth += 1
            elif mnemonic.startswith("pop"):
                if (mnemonic == "pop" and depth == 1 and ops
                        and ops[0].type == x86_const.X86_OP_REG):
                    reg = insn.reg_name(ops[0].reg)
                    if reg in self.reg_list32:
                        return insn, reg
                    return None
                depth -= 1
                if depth <= 0:
                    return None
            elif (mnemonic in ("sub", "add") and len(ops) >= 2
                  and ops[0].type == x86_const.X86_OP_REG
                  and insn.reg_name(ops[0].reg) == "esp"
                  and ops[1].type == x86_const.X86_OP_IMM):
                slots = ops[1].imm // 4
                if mnemonic == "sub":
                    depth += slots
                else:
                    depth -= slots
                    if depth <= 0:
                        return None
            elif (x86_const.X86_GRP_JUMP in insn.groups
                  or x86_const.X86_GRP_CALL in insn.groups
                  or x86_const.X86_GRP_RET in insn.groups
                  or mnemonic in ("ret", "retf", "jmp", "call")):
                return None
            address = insn.address + insn.size
        return None

    def find_data_and_refs(
        self,
        sections=None,
        *,
        base_address=0,
        include_immediates=True,
        include_getpc=True,
        **analysis_kwargs,
    ):
        """Find direct references to the data sections (32-bit).

        Besides explicit operands (immediates and absolute memory) it
        recognizes the position-independent getpc idiom ``call $+N; pop reg``
        and the late-pop variant. Instructions that start inside a data
        section (strings decoded as code by the linear sweep) are ignored,
        and branch/call targets are not treated as data pointers.
        """
        if sections is None:
            sections = symbolic_payload_coverage.find_data_sections(
                self.file,
                arch="x86",
                base_address=base_address,
                **analysis_kwargs,
            )

        self.data_sections = sections

        ranges = []
        for section in sections:
            start = int(section["address"])
            length = int(section["length"])
            if length > 0:
                ranges.append((start, start + length))

        ranges.sort()

        mask32 = 0xFFFFFFFF
        invalid = x86_const.X86_REG_INVALID
        xrefs = []
        seen = set()

        def containing_range(target):
            for start, end in ranges:
                if start > target:
                    break
                if start <= target < end:
                    return start, end
            return None

        def overlaps_data(insn):
            insn_end = insn.address + insn.size
            for start, end in ranges:
                if start >= insn_end:
                    break
                if end > insn.address and start < insn_end:
                    return True
            return False

        def add_xref(source, target):
            span = containing_range(target)
            if span is None:
                return
            xref = (source, target, span[1] - span[0])
            if xref not in seen:
                seen.add(xref)
                xrefs.append(xref)

        def decode_at(address):
            return self.decode_original_at(address)

        for entry in self.instructions:
            insn = entry.original_instruction

            # Capstone uses id=0 for the data produced by skipdata.
            if insn.id == 0 or insn.mnemonic == ".byte":
                continue

            if overlaps_data(insn):
                continue

            is_control_flow = (
                x86_const.X86_GRP_JUMP in insn.groups
                or x86_const.X86_GRP_CALL in insn.groups
                or x86_const.X86_GRP_BRANCH_RELATIVE in insn.groups
                or insn.mnemonic in (
                    "loop", "loope", "loopne", "jecxz", "jcxz",
                )
            )

            # `call target` whose return address is the start of a data
            # section and whose target is its end: the CPU pushes the data
            # address. This covers the classic `call $+5; pop reg`, the late
            # pop, and the 32-bit idiom where the pushed string address is
            # left on the stack as an argument for the resolved API.
            if include_getpc and insn.mnemonic == "call" and insn.operands:
                first = insn.operands[0]
                if first.type == x86_const.X86_OP_IMM:
                    return_address = (insn.address + insn.size) & mask32
                    span = containing_range(return_address)
                    if span is not None and span[0] == return_address:
                        callee = decode_at(first.imm & mask32)
                        if callee is not None and callee.address == span[1]:
                            add_xref(insn.address, return_address)

            for op in insn.operands:
                target = None

                if op.type == x86_const.X86_OP_IMM:
                    # Branch/call targets are code addresses, not pointers.
                    if (include_immediates and not is_control_flow
                            and insn.mnemonic.split()[0] in ("mov", "push")):
                        target = op.imm & mask32

                elif op.type == x86_const.X86_OP_MEM:
                    mem = op.mem

                    # FS/GS need the segment base at runtime.
                    if (mem.segment in (x86_const.X86_REG_FS,
                                        x86_const.X86_REG_GS)
                            and insn.id != x86_const.X86_INS_LEA):
                        continue

                    # An index register value is unknown.
                    if mem.index != invalid:
                        continue

                    if mem.base == invalid:
                        address_mask = (1 << (insn.addr_size * 8)) - 1
                        target = mem.disp & address_mask

                if target is not None:
                    add_xref(insn.address, target)

        self.data_xrefs = xrefs
        return xrefs

    # ------------------------------------------------------------------
    # Data extraction (opt-in with --extract-data)
    # ------------------------------------------------------------------

    def rebuild_instructions_from_bytes(self, code):
        """Re-disassemble the payload after a byte-level edit."""
        self.raw_code = bytes(code)
        self.instructions = []
        self.instr_dict = {}
        self.updated_instr_dict = {}
        self.short_label_table = []
        self.start_end_table = []
        self.jump_table = []
        for i in self.cs.disasm(self.raw_code, 0):
            instruction = Instruction(i, i, i, None, None)
            instruction.address_history.append(i.address)
            self.instructions.append(instruction)
            self.instr_dict[i.address] = instruction
            self.updated_instr_dict[i.address] = instruction
        for x, instr in enumerate(self.instructions):
            instr.new_bytes = instr.new_instruction.bytes
            if x == 0:
                continue
            instr.prev_instruction = self.instructions[x - 1]
            if x == len(self.instructions) - 1:
                continue
            instr.next_instruction = self.instructions[x + 1]
        self.sweep_coverage = sum(len(i.new_instruction.bytes)
                                  for i in self.instructions)
        self.sweep_tail = self.raw_code[self.sweep_coverage:]
        print(f"REBUILT {len(self.instructions)} INSTRUCTIONS "
              f"({self.sweep_coverage}/{len(self.raw_code)} bytes)")

    def _data_cache_key(self):
        return hashlib.sha256(self.raw_code).hexdigest()

    @staticmethod
    def _valid_cached_sections(sections):
        if not isinstance(sections, list):
            return False
        for section in sections:
            if not isinstance(section, dict):
                return False
            if not isinstance(section.get("address"), int):
                return False
            if not isinstance(section.get("length"), int) or section["length"] <= 0:
                return False
            if not isinstance(section.get("kind"), str):
                return False
        return True

    def _load_data_cache(self, cache_path, payload_hash, timeout):
        if not cache_path or not os.path.isfile(cache_path):
            return None
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[cache] cannot read {cache_path}: {e}; ignoring it")
            return None
        if not isinstance(data, dict) or \
                data.get("schema") != self.DATA_CACHE_SCHEMA:
            print(f"[cache] {cache_path}: unsupported schema; ignoring it")
            return None
        entry = (data.get("payloads", {}).get(payload_hash)
                 if isinstance(data.get("payloads"), dict) else None)
        if not isinstance(entry, dict):
            return None
        sections = entry.get("sections")
        if not self._valid_cached_sections(sections):
            print(f"[cache] {cache_path}: malformed entry; ignoring it")
            return None
        print(f"[cache] hit {payload_hash[:12]} in {cache_path} "
              f"({len(sections)} sections, "
              f"timeout={entry.get('analysis_timeout')}s, "
              f"created {entry.get('created_at', '?')})")
        print("[cache] using the stored sections; "
              "--refresh-data-cache re-runs the symbolic search")
        return sections

    def _save_data_cache(self, cache_path, payload_hash, sections, timeout):
        if not cache_path:
            return
        data = {"schema": self.DATA_CACHE_SCHEMA, "payloads": {}}
        if os.path.isfile(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if (isinstance(loaded, dict)
                        and loaded.get("schema") == self.DATA_CACHE_SCHEMA
                        and isinstance(loaded.get("payloads"), dict)):
                    data = loaded
            except Exception as e:
                print(f"[cache] cannot read {cache_path}: {e}; recreating it")
        data["payloads"][payload_hash] = {
            "payload": os.path.abspath(self.file),
            "size": len(self.raw_code),
            "arch": "x86",
            "base_address": 0,
            "analysis_timeout": timeout,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "sections": sections,
        }
        tmp_path = cache_path + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                f.write("\n")
            os.replace(tmp_path, cache_path)
            print(f"[cache] saved {payload_hash[:12]} to {cache_path}")
        except Exception as e:
            print(f"[cache] cannot write {cache_path}: {e}")
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    def analyze_data(self, *, timeout=120, print_strings=True,
                     cache_path="data_cache.json", use_cache=True,
                     refresh_cache=False):
        """Run (or reuse) the symbolic data discovery (32-bit)."""
        print("SYMBOLIC DATA ANALYSIS...")
        payload_hash = self._data_cache_key()
        sections = None
        if not use_cache:
            print("[cache] disabled")
        elif not refresh_cache:
            sections = self._load_data_cache(cache_path, payload_hash, timeout)
        else:
            print(f"[cache] refreshing entry for {payload_hash[:12]}")

        if sections is None:
            sections = symbolic_payload_coverage.find_data_sections(
                self.file,
                arch="x86",
                base_address=0,
                timeout=timeout,
                print_strings=print_strings,
            )
            if use_cache:
                self._save_data_cache(cache_path, payload_hash, sections,
                                      timeout)

        # The analyzer may classify only the tail of an inline string: the
        # linear sweep decodes its first bytes as code, so for the 32-bit
        # messagebox it reports "ageBox" (0xb8) instead of "MessageBox"
        # (0xb4). The `call` that skips the string is the proof of the real
        # boundaries, so align the section with it before the xref scan.
        sections = self._extend_sections_to_call_gaps(sections)

        xrefs = self.find_data_and_refs(sections=sections)
        self.data_sections = sections
        print(f"Data sections: {len(sections)}")
        for section in sections:
            print(f"  {section['address']:#x} ({section['length']} B) "
                  f"{section.get('kind')}")
        print(f"Data xrefs: {len(xrefs)}")
        for source, target, length in xrefs:
            print(f"  {source:#x} -> {target:#x} ({length} B)")
        return sections, xrefs

    def _extend_sections_to_call_gaps(self, sections):
        """Align analyzer sections with the ``call`` that points at them.

        A ``call target`` pushes its return address; when the target is the
        end of a data section and the return address falls before it, the
        whole ``[return address, target)`` range is the data the call refers
        to. The analyzer may have classified only the tail of it (the linear
        sweep can decode the first bytes as code), so extend the section to
        the return address when both the prefix and the section are
        printable. This is what makes the 32-bit messagebox caption
        (``MessageBox``) survive extraction and morphing.
        """
        if not sections:
            return sections

        result = [dict(section) for section in sections]
        changed = True
        while changed:
            changed = False
            for entry in self.instructions:
                insn = entry.original_instruction
                if insn.mnemonic != "call" or not insn.operands:
                    continue
                if insn.operands[0].type != x86_const.X86_OP_IMM:
                    continue
                return_address = insn.address + insn.size
                target = insn.operands[0].imm & 0xFFFFFFFF
                if target <= return_address:
                    continue
                for section in result:
                    start = int(section["address"])
                    end = start + int(section["length"])
                    if end != target:
                        continue
                    if not (return_address < start
                            and start - return_address <= 64):
                        continue
                    prefix = self.raw_code[return_address:start]
                    gap = self.raw_code[return_address:target]
                    if not prefix or not all(32 <= b < 127 for b in prefix):
                        continue
                    if not all(32 <= b < 127 or b == 0 for b in gap):
                        continue
                    section["address"] = return_address
                    section["length"] = target - return_address
                    section["kind"] = "ascii"
                    changed = True
                    break

        result.sort(key=lambda section: int(section["address"]))
        merged = []
        for section in result:
            start = int(section["address"])
            if merged:
                last_start = int(merged[-1]["address"])
                last_end = last_start + int(merged[-1]["length"])
                if last_start <= start < last_end:
                    continue
            merged.append(section)
        return merged

    def _data_preview(self, section):
        raw = section["bytes"]
        try:
            if section.get("kind") == "ascii":
                return raw[:-1].decode("ascii")
            if section.get("kind") == "utf16le":
                return raw[:-2].decode("utf-16-le")
        except UnicodeDecodeError:
            pass
        return raw[:24].hex(" ")

    def _classify_data_ref(self, source, target, section_start, section_length):
        """Classify one xref as getpc/getpc_stub/abs/imm or unsupported."""
        entry = self.instr_dict.get(source)
        if entry is None:
            return {"kind": "unsupported", "source": source,
                    "reason": "no instruction at source"}
        insn = entry.original_instruction
        mask32 = 0xFFFFFFFF
        delta = target - section_start

        if insn.mnemonic == "call" and insn.operands and \
                insn.operands[0].type == x86_const.X86_OP_IMM:
            if target == (source + insn.size) & mask32 and delta == 0:
                callee = self.decode_original_at(insn.operands[0].imm & mask32)
                if (callee is not None
                        and callee.address == section_start + section_length):
                    # The call skips the whole section and pushes its start
                    # address (classic pop, late pop, or API argument).
                    return {
                        "kind": "getpc", "source": source,
                        "instr": entry, "delta": 0,
                        "region_start": source,
                        "region_end": section_start + section_length,
                        "callee": callee.address,
                        "old_target": target,
                    }
            return {"kind": "unsupported", "source": source,
                    "reason": "call does not match a getpc data site"}

        for op_index, op in enumerate(insn.operands):
            if op.type == x86_const.X86_OP_MEM:
                mem = op.mem
                if mem.segment in (x86_const.X86_REG_FS,
                                   x86_const.X86_REG_GS):
                    continue
                if mem.index != x86_const.X86_REG_INVALID:
                    continue
                if mem.base == x86_const.X86_REG_INVALID:
                    address_mask = (1 << (insn.addr_size * 8)) - 1
                    if (mem.disp & address_mask) == target:
                        return {"kind": "abs", "source": source, "instr": entry,
                                "op_index": op_index, "delta": delta,
                                "old_disp": mem.disp, "old_target": target}
            elif op.type == x86_const.X86_OP_IMM:
                # Only instructions that can materialize an address.
                if insn.mnemonic.split()[0] not in ("mov", "push"):
                    continue
                if (op.imm & mask32) == target:
                    return {"kind": "imm", "source": source, "instr": entry,
                            "op_index": op_index, "delta": delta,
                            "old_imm": op.imm & mask32, "old_target": target}

        return {"kind": "unsupported", "source": source,
                "reason": "no supported operand references the data"}

    def extract_data(self, sections=None, xrefs=None, *, include_unknown=False,
                     timeout=120):
        """Move discovered data to the end of the payload (32-bit).

        The call of a getpc site is left in place during extraction; the
        finalize step turns it into a jmp to a 5-byte ``call consumer`` stub
        placed right before the moved data. The stub pushes the new data
        address and jumps to the original consumer, so no RIP-relative
        instruction is needed. Other supported references (absolute memory,
        mov/push immediates) are recorded and patched by finalize.
        """
        if self.extracted_data:
            raise RuntimeError("extract_data() already called")
        if sections is None:
            sections, xrefs = self.analyze_data(timeout=timeout,
                                                print_strings=False)
        elif xrefs is None:
            xrefs = self.find_data_and_refs(sections=sections)

        if self.instructions and \
                self.instructions[0].original_instruction.address != 0:
            raise RuntimeError("data extraction requires payload-relative "
                               "addresses (base 0)")

        # 1) candidate sections
        candidates = []
        for section in sections:
            start = int(section["address"])
            length = int(section["length"])
            if length <= 0:
                continue
            if start < 0 or start + length > len(self.raw_code):
                print(f"[extract] skip out-of-range section {start:#x}+{length}")
                continue
            kind = section.get("kind", "unknown")
            if kind == "outside_cfg" and not include_unknown:
                print(f"[extract] skip outside_cfg range {start:#x}+{length} "
                      "(pass --extract-unknown to move it)")
                continue
            candidates.append({
                "offset": start,
                "length": length,
                "bytes": bytes(self.raw_code[start:start + length]),
                "kind": kind,
                "new_address": None,
                "move": True,
                "refs": [],
                "getpc": None,
            })
        candidates.sort(key=lambda item: item["offset"])

        for first, second in zip(candidates, candidates[1:]):
            if first["offset"] + first["length"] > second["offset"]:
                raise RuntimeError(
                    f"overlapping data candidates {first['offset']:#x} and "
                    f"{second['offset']:#x}; refusing to move them")

        def candidate_index(target):
            for index, item in enumerate(candidates):
                if item["offset"] <= target < item["offset"] + item["length"]:
                    return index
            return None

        for source, target, _length in xrefs:
            index = candidate_index(target)
            if index is None:
                continue
            item = candidates[index]
            item["refs"].append(
                self._classify_data_ref(source, target, item["offset"],
                                        item["length"]))

        # 2) keep unsafe sections in place
        for item in candidates:
            if not item["refs"]:
                print(f"[extract] keep {item['offset']:#x}+{item['length']}: "
                      "no verified reference (moving it could break the payload)")
                item["move"] = False
                continue
            unsupported = [ref for ref in item["refs"]
                           if ref["kind"] == "unsupported"]
            if unsupported:
                print(f"[extract] keep {item['offset']:#x}+{item['length']}: "
                      f"{unsupported[0].get('reason')}")
                item["move"] = False
                continue
            getpc_refs = [ref for ref in item["refs"]
                          if ref["kind"] in ("getpc", "getpc_stub")]
            if len(getpc_refs) > 1:
                print(f"[extract] keep {item['offset']:#x}: multiple getpc sites")
                item["move"] = False
                continue
            if getpc_refs:
                ref = getpc_refs[0]
                if ref["region_end"] - (ref["region_start"] + 5) < 1:
                    print(f"[extract] keep {item['offset']:#x}: getpc region too small")
                    item["move"] = False
                    continue
                if ref["instr"].new_instruction.size != 5:
                    print(f"[extract] keep {item['offset']:#x}: getpc call is not 5 bytes")
                    item["move"] = False
                    continue
                item["getpc"] = ref

        # 3) getpc rewrite regions must not overlap each other or other data
        regions = sorted(
            ((item["getpc"]["region_start"], item["getpc"]["region_end"], item)
             for item in candidates if item["move"] and item.get("getpc")),
            key=lambda entry: entry[0])
        for index in range(len(regions) - 1):
            if regions[index][1] > regions[index + 1][0]:
                raise RuntimeError("overlapping getpc rewrite regions")
        for start, end, owner in regions:
            conflict = False
            for item in candidates:
                if item is owner:
                    continue
                if item["offset"] < end and start < item["offset"] + item["length"]:
                    print(f"[extract] keep {owner['offset']:#x}: it overlaps "
                          f"another data candidate at {item['offset']:#x}")
                    conflict = True
            if conflict:
                owner["move"] = False

        def crosses_instruction(start, end):
            for entry in self.instructions:
                insn = entry.original_instruction
                insn_start = insn.address
                insn_end = insn.address + insn.size
                if insn_start < start < insn_end:
                    return True
                if insn_start < end < insn_end:
                    return True
            return False

        for item in candidates:
            if not item["move"] or item.get("getpc"):
                continue
            if crosses_instruction(item["offset"],
                                   item["offset"] + item["length"]):
                print(f"[extract] keep {item['offset']:#x}: an instruction "
                      "crosses its boundary")
                item["move"] = False

        movable = [item for item in candidates if item["move"]]
        if not movable:
            print("[extract] no movable data sections")
            return []

        # 4) build the stripped code (same length, data replaced by NOPs)
        new_code = bytearray(self.raw_code)
        for item in movable:
            ref = item.get("getpc")
            if ref:
                # keep the call; only the inline data becomes NOPs
                for offset in range(ref["region_start"] + 5, ref["region_end"]):
                    new_code[offset] = 0x90
            else:
                for offset in range(item["offset"],
                                    item["offset"] + item["length"]):
                    new_code[offset] = 0x90

        self.rebuild_instructions_from_bytes(new_code)
        if self.sweep_coverage != len(self.raw_code):
            raise RuntimeError(
                f"disassembly covered {self.sweep_coverage} of "
                f"{len(self.raw_code)} bytes; refusing to extract data from a "
                "partially disassembled payload")

        # 5) register fixups on the rebuilt instructions
        self.extracted_data = [{
            "offset": item["offset"],
            "length": item["length"],
            "bytes": item["bytes"],
            "kind": item["kind"],
            "new_address": None,
        } for item in movable]
        section_index = {id(item): index for index, item in enumerate(movable)}
        self.data_ref_fixups = []

        for item in movable:
            index = section_index[id(item)]
            for ref in item["refs"]:
                if ref["kind"] in ("getpc", "getpc_stub"):
                    instr = self.instr_dict.get(ref["region_start"])
                    if instr is None or instr.new_instruction.mnemonic != "call" \
                            or instr.new_instruction.size != 5:
                        raise RuntimeError(
                            f"getpc rewrite at {ref['region_start']:#x} "
                            "did not keep a 5-byte call")
                    fixup = {"kind": "getpc", "section": index,
                             "source": ref["source"], "delta": 0,
                             "instr": instr, "callee": ref["callee"],
                             "old_target": ref["old_target"]}
                    instr.protected = True
                else:
                    instr = self.instr_dict.get(ref["source"])
                    if instr is None:
                        raise RuntimeError(
                            f"instruction at {ref['source']:#x} disappeared")
                    self._check_rebuilt_reference(instr.new_instruction, ref)
                    fixup = {"kind": ref["kind"], "section": index,
                             "source": ref["source"], "delta": ref["delta"],
                             "instr": instr,
                             "op_index": ref["op_index"],
                             "old_disp": ref.get("old_disp"),
                             "old_imm": ref.get("old_imm")}
                instr.data_ref_fixup = fixup
                self.data_ref_fixups.append(fixup)

        print(f"[extract] moving {len(self.extracted_data)} section(s), "
              f"{sum(section['length'] for section in self.extracted_data)} B")
        for section in self.extracted_data:
            print(f"  {section['offset']:#x} ({section['length']} B "
                  f"{section['kind']}) {self._data_preview(section)!r}")
        print(f"[extract] references to rewrite: {len(self.data_ref_fixups)}")
        return self.extracted_data

    def _check_rebuilt_reference(self, insn, ref):
        """Confirm the rebuilt instruction still points at the old data."""
        kind = ref["kind"]
        if kind == "abs":
            mem = insn.operands[ref["op_index"]].mem
            address_mask = (1 << (insn.addr_size * 8)) - 1
            actual = mem.disp & address_mask
        elif kind == "imm":
            actual = insn.operands[ref["op_index"]].imm & 0xFFFFFFFF
        else:
            raise RuntimeError(f"unknown reference kind {kind}")
        if actual != ref["old_target"]:
            raise RuntimeError(
                f"reference at {ref['source']:#x} changed during the rewrite")

    @staticmethod
    def _replace_first_hex(text, value):
        match = re.search(r"0x[0-9a-fA-F]+", text)
        if match is None:
            return None
        return f"{text[:match.start()]}{hex(value)}{text[match.end():]}"

    def _patch_memory_reference(self, instr, insn_address, fixup, target):
        insn = instr.new_instruction
        op_str = self._replace_first_hex(insn.op_str, target)
        if op_str is None:
            raise RuntimeError(
                f"cannot locate displacement in {insn.mnemonic} {insn.op_str}")
        text = f"{insn.mnemonic} {op_str}"
        asm, _ = self.ks.asm(text, insn_address)
        raw = bytes(asm) if asm else b""
        if len(raw) != insn.size:
            raise RuntimeError(
                f"reference at {fixup['source']:#x} changed size: "
                f"{insn.mnemonic} {insn.op_str} -> {text}")
        new_instruction = next(self.cs.disasm(raw, insn_address, count=1), None)
        if new_instruction is None:
            raise RuntimeError(f"cannot decode rewritten {text}")
        instr.new_instruction = new_instruction
        instr.new_bytes = raw

    def _patch_immediate_reference(self, instr, insn_address, fixup, target):
        insn = instr.new_instruction
        op_str = self._replace_first_hex(insn.op_str, target)
        if op_str is None:
            raise RuntimeError(
                f"cannot locate immediate in {insn.mnemonic} {insn.op_str}")
        text = f"{insn.mnemonic} {op_str}"
        asm, _ = self.ks.asm(text, insn_address)
        raw = bytes(asm) if asm else b""
        if len(raw) != insn.size:
            raise RuntimeError(
                f"immediate reference at {fixup['source']:#x} changed size: "
                f"{insn.mnemonic} {insn.op_str} -> {text}")
        new_instruction = next(self.cs.disasm(raw, insn_address, count=1), None)
        if new_instruction is None:
            raise RuntimeError(f"cannot decode rewritten {text}")
        instr.new_instruction = new_instruction
        instr.new_bytes = raw

    def _verify_data_ref(self, instr, insn_address, fixup, target):
        insn = instr.new_instruction
        kind = fixup["kind"]
        if kind == "abs":
            mem = insn.operands[fixup["op_index"]].mem
            address_mask = (1 << (insn.addr_size * 8)) - 1
            actual = mem.disp & address_mask
        elif kind == "imm":
            actual = insn.operands[fixup["op_index"]].imm & 0xFFFFFFFF
        else:
            raise RuntimeError(f"unknown fixup kind {kind}")
        if actual != target:
            raise RuntimeError(
                f"reference {fixup['source']:#x} points at {actual:#x} "
                f"instead of {target:#x}")

    def finalize_data_refs(self):
        """Lay out the extracted data and rewrite every reference.

        Must be called after the last morphing step: the final instruction
        addresses determine the stub/jmp displacements.
        """
        if not self.extracted_data:
            return
        if self.data_refs_finalized:
            return

        addresses = {}
        address = 0
        for instr in self.instructions:
            addresses[id(instr)] = address
            address += len(instr.new_instruction.bytes)
        code_length = address

        for fixup in self.data_ref_fixups:
            if fixup["instr"] not in self.instructions:
                raise RuntimeError(
                    f"instruction at {fixup['source']:#x} disappeared during "
                    "morphing; cannot fix its data reference")

        if self.pii_enabled:
            # write_strange_file() places the PII instruction map at
            # self.mem_address; the data blob goes after the map (4-byte
            # entries in 32-bit mode).
            map_start = self.mem_address
            map_size = 4 * len(self.instr_mapping)
            data_base = map_start + map_size
            pad = (-data_base) % 16
            data_start = data_base + pad
        else:
            data_start = code_length + ((-code_length) % 16)
            pad = data_start - code_length

        by_original = {instr.original_instruction.address: instr
                       for instr in self.instructions}
        stub_indices = {fixup["section"] for fixup in self.data_ref_fixups
                        if fixup["kind"] == "getpc"}

        cursor = data_start
        for index, section in enumerate(self.extracted_data):
            if index in stub_indices:
                # Reserve 5 bytes for the call stub placed just before this
                # section: the stub's return address must be the section start.
                cursor += 5
            section["new_address"] = cursor
            cursor += section["length"]
        blob_start = data_start

        stub_bytes = {}

        for fixup in self.data_ref_fixups:
            instr = fixup["instr"]
            insn_address = addresses[id(instr)]
            section = self.extracted_data[fixup["section"]]
            target = section["new_address"] + fixup["delta"]
            if fixup["kind"] == "getpc":
                stub_addr = target - 5
                jmp_disp = stub_addr - (insn_address + 5)
                raw = b"\xE9" + (jmp_disp & 0xFFFFFFFF).to_bytes(4, "little")
                new_instruction = next(
                    self.cs.disasm(raw, insn_address, count=1), None)
                if new_instruction is None or new_instruction.mnemonic != "jmp":
                    raise RuntimeError(
                        f"cannot build the getpc jmp at {insn_address:#x}")
                instr.new_instruction = new_instruction
                instr.new_bytes = raw
                callee_instr = by_original.get(fixup["callee"])
                if callee_instr is None:
                    raise RuntimeError(
                        f"getpc callee {fixup['callee']:#x} disappeared")
                callee_addr = addresses[id(callee_instr)]
                call_disp = callee_addr - (stub_addr + 5)
                stub_bytes[stub_addr] = b"\xE8" + \
                    (call_disp & 0xFFFFFFFF).to_bytes(4, "little")
                if (instr.new_instruction.operands[0].imm
                        & 0xFFFFFFFF) != stub_addr:
                    raise RuntimeError("getpc jmp target mismatch")
                if stub_addr + 5 != section["new_address"]:
                    raise RuntimeError("getpc stub is not adjacent to data")
                continue
            elif fixup["kind"] == "abs":
                self._patch_memory_reference(instr, insn_address, fixup, target)
            elif fixup["kind"] == "imm":
                self._patch_immediate_reference(instr, insn_address, fixup,
                                                target)
            self._verify_data_ref(instr, insn_address, fixup, target)

        self.final_code_len = code_length
        self.final_data_pad = b"\x90" * pad
        blob_parts = []
        for index, section in enumerate(self.extracted_data):
            if index in stub_indices:
                stub_addr = section["new_address"] - 5
                blob_parts.append(stub_bytes[stub_addr])
            blob_parts.append(section["bytes"])
        self.final_data_blob = b"".join(blob_parts)
        self.data_refs_finalized = True

        code_bytes = b"".join(instr.new_instruction.bytes
                              for instr in self.instructions)
        for section in self.extracted_data:
            if len(section["bytes"]) >= 4 and section["bytes"] in code_bytes:
                print(f"[extract] WARNING: {section['offset']:#x} is still "
                      "present in the code area")
            blob_offset = section["new_address"] - blob_start
            if self.final_data_blob[blob_offset:blob_offset + section["length"]] \
                    != section["bytes"]:
                raise RuntimeError(
                    f"data section {section['offset']:#x} corrupted in the blob")

        if self.pii_enabled:
            map_size = 4 * len(self.instr_mapping)
            total = self.mem_address + map_size + pad + len(self.final_data_blob)
            print(f"[extract] PII code {code_length} B + map {map_size} B at "
                  f"{self.mem_address:#x} + pad {pad} B + "
                  f"data {len(self.final_data_blob)} B = {total} B")
        else:
            print(f"[extract] code {code_length} B + pad {pad} B + "
                  f"data {len(self.final_data_blob)} B = "
                  f"{code_length + pad + len(self.final_data_blob)} B")
        for section in self.extracted_data:
            print(f"[extract] data {section['offset']:#x} -> "
                  f"{section['new_address']:#x} ({section['length']} B)")
        for fixup in self.data_ref_fixups:
            instr = fixup["instr"]
            section = self.extracted_data[fixup["section"]]
            print(f"[extract] ref {fixup['source']:#x} "
                  f"(now {addresses[id(instr)]:#x}): "
                  f"{instr.new_instruction.mnemonic} "
                  f"{instr.new_instruction.op_str} -> "
                  f"{section['new_address'] + fixup['delta']:#x}")

    def pii_dispatcher_v2(self):
        """32-bit indexed dispatcher, extraction-compatible in layout terms.

        Handlers are shuffled except the entry. Direct branch/call targets are
        handler starts. Remote call/pop getpc becomes a base-relative
        call/pop/lea unit; extracted data getpc uses the same unit shape.
        """
        if not self.instructions:
            return

        old = list(self.instructions)
        address_to_instr = {
            instr.new_instruction.address: instr for instr in old
        }
        custom_getpc = {}
        for index, instr in enumerate(old):
            if instr.new_instruction.mnemonic != "call":
                continue
            # a call rewritten for data extraction is handled by
            # finalize_data_refs(); do not turn it into a getpc unit
            if getattr(instr, "protected", False) or instr.data_ref_fixup:
                continue
            operands = instr.new_instruction.operands
            if not operands or operands[0].type != x86_const.X86_OP_IMM:
                continue
            target = address_to_instr.get(operands[0].imm)
            if target is None or target.new_instruction.mnemonic != "pop":
                continue
            if target.new_instruction.op_str not in (
                    "eax", "ebx", "ecx", "edx", "esi", "edi", "ebp", "esp"):
                # data bytes can decode as pop es/ss/...; not a code getpc
                continue
            fallthrough = (old[index + 1] if index + 1 < len(old)
                           else None)
            if fallthrough is None or target is fallthrough:
                continue
            after_pop = target.next_instruction
            if after_pop is None or after_pop not in old:
                continue
            custom_getpc[instr] = (target.new_instruction.op_str,
                                   fallthrough, after_pop)

        terminator = self._pii_single_insn_32("ret", 0)
        getpc_fixups = []
        getpc_units = {}
        for instr, (reg, fallthrough, after_pop) in custom_getpc.items():
            # Base-relative getpc: call $+5/pop gives the runtime address of
            # the pop; lea adds the handler offset. This stays ASLR-safe.
            placeholder = self._pii_call_next_32()
            pop_instr = self._pii_single_insn_32(f"pop {reg}", 0)
            # disp32 placeholder: the final lea must keep the same size, so
            # it is assembled with a placeholder too and patched in place.
            lea_instr = self._pii_single_insn_32(
                f"lea {reg}, [{reg} + 0x11111111]", 0)
            instr.new_instruction = placeholder.new_instruction
            pop_instr.pii_group = True
            lea_instr.pii_group = True
            instr.pii_group = True
            getpc_units[instr] = (pop_instr, lea_instr, reg, fallthrough)
            getpc_fixups.append((lea_instr, pop_instr, reg, fallthrough))
            self.short_label_table = [
                item for item in self.short_label_table
                if item[0] is not instr]

        groups = []
        index = 0
        while index < len(old):
            if old[index] in getpc_units:
                pop_instr, lea_instr, reg, fallthrough = getpc_units[old[index]]
                group = [old[index], pop_instr, lea_instr]
                index += 1
            elif old[index].pii_group:
                group = [old[index]]
                cursor = index + 1
                while cursor < len(old) and old[cursor].pii_group:
                    group.append(old[cursor])
                    cursor += 1
                index = cursor
            elif old[index].bad_expanded:
                group = [old[index]]
                cursor = index + 1
                while cursor < len(old) and old[cursor].bad_expanded:
                    group.append(old[cursor])
                    cursor += 1
                index = cursor
            else:
                group = [old[index]]
                index += 1
            groups.append(group)

        instr_unit = {}
        for unit_index, group in enumerate(groups):
            for instr in group:
                instr_unit[id(instr)] = unit_index

        records = []
        for unit_index, group in enumerate(groups):
            if group[0] in custom_getpc:
                after_pop = custom_getpc[group[0]][2]
                next_index = instr_unit[id(after_pop)]
            else:
                next_index = (unit_index + 1
                              if unit_index + 1 < len(groups)
                              else len(groups))
            records.append((unit_index, group, next_index))

        first = records[0]
        rest = records[1:]
        random.shuffle(rest)
        ordered = [first] + rest

        handlers = []
        stub_jumps = []
        for unit_index, group, next_index in ordered:
            handlers.extend(group)
            flags = self._pii_single_insn_32("pushfd", 0)
            push = self._pii_single_insn_32(f"push {0x3e8 + next_index}", 0)
            jump = self._pii_single_insn_32("jmp 0", 0)
            handlers.extend([flags, push, jump])
            stub_jumps.append(jump)
        handlers.append(terminator)

        stub_addr_guess = sum(len(x.new_instruction.bytes) for x in handlers)
        stub_placeholder = []
        for capstone_instr in self._pii_stub_insns_32(0, stub_addr_guess):
            instr = Instruction(capstone_instr, capstone_instr,
                                capstone_instr, None, None)
            instr.address_history.append(capstone_instr.address)
            stub_placeholder.append(instr)
        handlers.extend(stub_placeholder)

        self.instructions = handlers
        for x, instr in enumerate(self.instructions):
            instr.prev_instruction = (self.instructions[x - 1] if x > 0
                                      else None)
            instr.next_instruction = (self.instructions[x + 1]
                                      if x + 1 < len(self.instructions)
                                      else None)

        for jump in stub_jumps:
            self.short_label_table.append((jump, stub_placeholder[0]))

        self.update_label_table()

        addresses = {}
        address = 0
        for instr in self.instructions:
            addresses[id(instr)] = address
            address += len(instr.new_instruction.bytes)

        for lea_instr, pop_instr, reg, fallthrough in getpc_fixups:
            addr = addresses[id(lea_instr)]
            here = addresses[id(pop_instr)]
            target = addresses[id(fallthrough)]
            displacement = target - here
            asm = self._lea_reg_disp32(reg, displacement, addr)
            for capstone_instr in self.cs.disasm(bytes(asm), addr):
                lea_instr.new_instruction = capstone_instr
                break

        stub_addr = addresses[id(stub_placeholder[0])]
        stub_size = sum(len(x.new_instruction.bytes)
                        for x in stub_placeholder)
        map_addr = stub_addr + stub_size

        here_instr = next(x for x in stub_placeholder
                          if x.new_instruction.mnemonic == "pop")
        map_displacement = map_addr - here_instr.new_instruction.address
        new_stub = self._pii_stub_insns_32(map_displacement, stub_addr)
        if len(new_stub) != len(stub_placeholder):
            raise RuntimeError("PII32 stub size changed during layout")
        for instr, capstone_instr in zip(stub_placeholder, new_stub):
            instr.new_instruction = capstone_instr

        entries = []
        for unit_index, group, next_index in records:
            entries.append((unit_index,
                            addresses[id(group[0])] - map_addr))
        entries.append((len(records),
                        addresses[id(terminator)] - map_addr))
        self.instr_mapping = entries
        self.mem_address = map_addr
        self.pii_enabled = True
        print(f"[pii32-v2] {len(records)} units, map at {map_addr:#x}, "
              f"{len(entries)} entries, shuffled")

    def pii_permute_instructions(self):
        if not self.instructions:
            return 0

        original = list(self.instructions)
        ret_instr = None
        asm, _ = self.ks.asm("ret", 0)
        for capstone_instr in self.cs.disasm(bytes(asm), 0):
            ret_instr = Instruction(capstone_instr, capstone_instr,
                                    capstone_instr, None, None)
            ret_instr.address_history.append(capstone_instr.address)
            break

        slots = []
        index = 0
        while index < len(original):
            group = [original[index]]
            if original[index].pii_group:
                cursor = index + 1
                while cursor < len(original) and original[cursor].pii_group:
                    group.append(original[cursor])
                    cursor += 1
                index = cursor
            elif original[index].bad_expanded:
                cursor = index + 1
                while (cursor < len(original)
                       and original[cursor].bad_expanded):
                    group.append(original[cursor])
                    cursor += 1
                index = cursor
            else:
                index += 1

            next_instr = (original[index] if index < len(original)
                          else ret_instr)
            last = group[-1]
            address = (last.new_instruction.address
                       + last.new_instruction.size)
            asm, _ = self.ks.asm(f"jmp {address}", address)
            jmp_instr = None
            for capstone_instr in self.cs.disasm(bytes(asm), address):
                jmp_instr = Instruction(capstone_instr, capstone_instr,
                                        capstone_instr, None, None)
                jmp_instr.address_history.append(capstone_instr.address)
                break
            slot = list(group)
            if jmp_instr is not None and next_instr is not None:
                slot.append(jmp_instr)
                self.short_label_table.append((jmp_instr, next_instr))
            slots.append(slot)

        first = slots[0]
        rest = slots[1:]
        random.shuffle(rest)
        self.instructions = [instr for slot in [first] + rest for instr in slot]
        if ret_instr is not None:
            self.instructions.append(ret_instr)

        for x, instr in enumerate(self.instructions):
            instr.prev_instruction = (self.instructions[x - 1] if x > 0
                                      else None)
            instr.next_instruction = (self.instructions[x + 1]
                                      if x + 1 < len(self.instructions)
                                      else None)
        print(f"[ip] permuted {len(original)} instructions into "
              f"{len(self.instructions)} slots")
        return len(self.instructions)

    def brain_obfuscator(self):
        brain_shuffle = True
        # salva indirizzi di inizio blocco e poi shuffla i blocchi
        calc_base_str = f"call 0x1000"
        asm, _ = self.ks.asm(calc_base_str,0x0)
        bytes_arr = bytearray(asm)
        for x,i in enumerate(self.cs.disasm(bytes_arr,0x0)):
            insr = Instruction(i,i,i,None,None)
            self.insert_instruction(0,insr)

        # self.update_instr()


        self.brain_adjust()


        if brain_shuffle == True:
            self.shuffle_brain_blocks()


        self.update_label_table()

        unused_regs = self.check_unused_registers()

        random_unused_reg = random.choice(unused_regs)


        # estimated_stub_addr = self.estimate_stub_address()

        self.payload_size = 0
        for instr in self.instructions:
            self.payload_size += len(instr.new_instruction.bytes)
        
        
        print("Estimated stub address: ",self.stub_address)
        print("Payload SIZE: ", self.payload_size)
        nop_sled_size = self.stub_address - self.payload_size

        print("NOP SLED SIZE: ",nop_sled_size)

        instr_number = len(self.instructions)

        for i in range(nop_sled_size):
            nop = bytearray([0x90])

            for instr in self.cs.disasm(nop, self.payload_size + i):
                insr = Instruction(instr,instr,instr,None,None)
                self.insert_instruction(instr_number + i, insr)
                instr_number += 1

        instruction_num = 0
        for x,instr in enumerate(self.instructions):
            if x == 0:
                continue
            if instr.new_instruction.mnemonic == "pop" and instr.new_instruction.op_str == "eax" and x % self.wrap_instruction_num == 1:
                
                self.instr_mapping.append((x,instr.new_instruction.address))
            instruction_num += 1

        for x,instr in enumerate(self.instructions):
            index  = 0
            if x == 0:
                continue
            if instr.new_instruction.mnemonic == "pop" and instr.new_instruction.op_str == "eax" and x % self.wrap_instruction_num == 1:
                for instr2 in self.instructions[x:x+5]:
                    if instr2.new_instruction.mnemonic == "push" and instr2.next_instruction.new_instruction.mnemonic == "jmp":
                        # print("push found")
                        index = int(instr2.new_instruction.op_str,16) - 0x3e8
                        # print("index: ",index)
                        self.instr_mapping[index] = (index,instr.new_instruction.address)
        # sort instr_mapping by index
        self.instr_mapping.sort(key=lambda x: x[0])

        # print instr mapping to a file
        with open('instr_mapping.txt', 'w') as f:
            for entry in self.instr_mapping:
                f.write(f"{entry[0]} {hex(entry[1])}\n")
            
            f.close()

        
        
        # write map to file

        self.stub_size = self.estimate_stub_size()
        self.stub2_size = self.estimate_stub2_size()
        print("STUB SIZE: ",self.stub_size)




        mem_size_on_disk = instruction_num * 4

        self.stub2_address = self.stub_address + self.stub_size
        self.stub2_address = self.stub2_address + (0x10 - (self.stub2_address % 0x10))

        

        self.mem_address = self.stub2_address + self.stub2_size
        self.mem_address = self.mem_address + (100 - (self.mem_address % 100)) + 0x100

        self.init_address = self.stub2_address + self.stub2_size + 0x10

        print("MEMORY ADDRESS: ",hex(self.mem_address))
        padding = self.mem_address - self.stub_address - self.stub_size
        print("PADDING SIZE: ",padding)
        print("init address: ",hex(self.init_address))

        # self.stub2_address = self.counter_address + 0x10
        # self.stub2_address = self.stub2_address + (0x10 - (self.stub2_address % 0x10))


        init_addr_offset = self.init_address - (self.stub_address + 0x14) 
        print("INIT ADDR OFFSET: ",init_addr_offset)    

        stub_str = f'''
        push eax;
        push ecx;
        mov ecx, [esp + 0x8]
        pushfd;
        sub ecx, 0x3e8;
        inc ecx;

        call {self.stub_address + 0x14};
        pop eax;

        mov eax, [eax + {init_addr_offset}];
        mov ecx, [eax + {self.mem_address} - 5 + ecx * 4];
        sub ecx, 0x5
        add eax, ecx
        popfd;
        pop ecx;
        jmp eax;
        '''

        stub2_str = f'''
        pop {random_unused_reg};
        mov [{random_unused_reg} - 5 + {self.init_address}], {random_unused_reg};
        push {random_unused_reg};
        jmp {random_unused_reg};
        '''


        asm, _ = self.ks.asm(stub_str,self.stub_address)

        bytes_arr = bytearray(asm)
        for x,i in enumerate(self.cs.disasm(bytes_arr,self.stub_address)):
            insr = Instruction(i,i,i,None,None)
            self.insert_instruction(instr_number + x , insr)
            instr_number += 1

        nop_sled_size2 = self.stub2_address - (self.stub_address + self.stub_size)

        print("NOP SLED SIZE 2: ",nop_sled_size2)

        print("STUB2 ADDRESS: ",hex(self.stub2_address))
        for i in range(nop_sled_size2):
            nop = bytearray([0x90])
            for instr in self.cs.disasm(nop, (self.stub_address + self.stub_size + i)):
                insr = Instruction(instr,instr,instr,None,None)
                self.insert_instruction(instr_number + i, insr)
                instr_number += 1

        asm2, _ = self.ks.asm(stub2_str,self.stub2_address)
        bytes_arr2 = bytearray(asm2)

        for x,i in enumerate(self.cs.disasm(bytes_arr2,self.stub2_address)):
            insr = Instruction(i,i,i,None,None)
            self.insert_instruction(instr_number + x , insr)
            instr_number += 1

        new_first_instr_str = f"call {self.stub2_address}"
        asm3, _ = self.ks.asm(new_first_instr_str,0x0)
        bytes_arr3 = bytearray(asm3)
        for x,i in enumerate(self.cs.disasm(bytes_arr3,0x0)):
            self.instructions[0].new_instruction = i
        self.re_adjust_brain()


    def eliminate_bad_instructions(self):
        """Expand jecxz/jcxz/loop-family short branches to a 12-byte trampoline.

        A+0: short branch +5
        A+2: near jmp fallthrough
        A+7: near jmp target
        A+12: fallthrough
        """
        opcodes = {
            "jrcxz": 0xE3, "jecxz": 0xE3, "jcxz": 0xE3,
            "loop": 0xE2, "loope": 0xE1, "loopne": 0xE0,
        }
        expanded = 0
        while True:
            found = False
            for index, instr in enumerate(self.instructions):
                mnemonic = instr.new_instruction.mnemonic
                if mnemonic not in opcodes:
                    continue
                if instr.bad_expanded:
                    continue
                entry = next((item for item in self.short_label_table
                              if item[0] is instr), None)
                if entry is None or index + 1 >= len(self.instructions):
                    print(f"[bad] {instr.new_instruction.address:#x} "
                          f"{mnemonic}: no label/fallthrough, skipped")
                    continue
                target_instr = entry[1]
                fallthrough = self.instructions[index + 1]
                address = instr.new_instruction.address

                sequence = bytearray([opcodes[mnemonic], 0x05, 0xE9])
                sequence += (5).to_bytes(4, "little", signed=True)
                sequence += b"\xE9"
                sequence += (0).to_bytes(4, "little", signed=True)

                sequence_instrs = []
                for capstone_instr in self.cs.disasm(bytes(sequence), address):
                    new_instr = Instruction(capstone_instr, capstone_instr,
                                            capstone_instr, None, None)
                    new_instr.address_history.append(capstone_instr.address)
                    sequence_instrs.append(new_instr)
                if len(sequence_instrs) != 3:
                    raise RuntimeError(
                        f"cannot build the trampoline for {mnemonic} at "
                        f"{address:#x}")

                self.short_label_table = [
                    item for item in self.short_label_table
                    if item[0] is not instr]

                if index == 0:
                    self.instructions.pop(0)
                    if self.instructions:
                        self.instructions[0].prev_instruction = None
                else:
                    self.eliminate_instruction(index)
                for offset, sequence_instr in enumerate(sequence_instrs):
                    self.insert_instruction(index + offset, sequence_instr)
                    sequence_instr.bad_expanded = True

                self.short_label_table.append(
                    (sequence_instrs[0], sequence_instrs[2]))
                self.short_label_table.append(
                    (sequence_instrs[1], fallthrough))
                self.short_label_table.append(
                    (sequence_instrs[2], target_instr))

                for position, item in enumerate(self.short_label_table):
                    if item[1] is instr:
                        self.short_label_table[position] = (
                            item[0], sequence_instrs[0])

                expanded += 1
                found = True
                break
            if not found:
                break
        print(f"[bad] expanded {expanded} short branch(es)")
        return expanded

    def mark_data_ranges32(self):
        """Mark printable inline data so -eq/-nop do not rewrite it.

        This is a conservative static heuristic: printable runs of four or
        more bytes are treated as data. It is not a full CFG classifier, but
        it protects the strings/hashes embedded in 32-bit shellcode.
        """
        raw = self.raw_code
        ranges = []
        index = 0
        while index < len(raw):
            if 32 <= raw[index] < 127:
                end = index
                while end < len(raw) and 32 <= raw[end] < 127:
                    end += 1
                if end - index >= 4:
                    if end < len(raw) and raw[end] == 0:
                        end += 1
                    ranges.append((index, end))
                index = end
            else:
                index += 1
        self.data_ranges32 = ranges
        self.nop_min_address = max((end for _start, end in ranges), default=0)
        self.data_instruction_ids = set()
        for instr in self.instructions:
            address = instr.original_instruction.address
            if any(start <= address < end for start, end in ranges):
                self.data_instruction_ids.add(id(instr))
        if ranges:
            print(f"[data32] protected {len(ranges)} printable range(s), "
                  f"{len(self.data_instruction_ids)} instruction(s)")

        # Do not insert random NOPs inside a pushal/popal resolver frame:
        # the frame and its tight hash loops are sensitive to layout changes.
        self.nop_skip_ids = set()
        inside_frame = False
        for instr in self.instructions:
            mnemonic = instr.new_instruction.mnemonic
            if mnemonic in ("pushal", "pushad"):
                inside_frame = True
            if inside_frame:
                self.nop_skip_ids.add(id(instr))
            if mnemonic in ("popal", "popad"):
                inside_frame = False

    def equal_instructions(self):
        change_num = 0
        bytes_added = 0
        for num_instr,instr in enumerate(self.instructions):
            if id(instr) in self.data_instruction_ids:
                continue
            #substitue xor reg,rex with mov reg,0x0

            prob = random.randint(0,100)
            if prob > 50:
                continue

            # if change_num > 10:
            #     break

            if(instr.old_instruction.id == x86_const.X86_INS_XOR and instr.old_instruction.operands[0].type == x86_const.X86_OP_REG and instr.old_instruction.operands[1].type == x86_const.X86_OP_REG):
                if instr.old_instruction.operands[0].reg == instr.old_instruction.operands[1].reg:
                    print("ADDRESS DEL PRIMO XOR EAX,EAX: ", hex(instr.old_instruction.address))
                    str_instr = f"mov {instr.old_instruction.reg_name(instr.old_instruction.operands[0].reg)},0x0"
                    #str_instr = f"sub eax,eax"

                    asm, _ = self.ks.asm(str_instr, instr.old_instruction.address)

                    bytes_arr = bytearray(asm)


                    for i in self.cs.disasm(bytes_arr,instr.new_instruction.address):
                        print("vecchia istruzione: ", instr.old_instruction.mnemonic, instr.old_instruction.op_str)
                        print("nuova istruzione: ", i.mnemonic, i.op_str)
                        instr.new_instruction = i
                        #instr.update_address(num_bytes)    
                    #self.update_old_instructions(instr)             
                    bytes_added += (len(bytes_arr) - len(instr.old_instruction.bytes)) 
                    change_num += 1

            #substitute add reg, x  with sub reg, -x
            elif (instr.old_instruction.id == x86_const.X86_INS_ADD and instr.old_instruction.operands[0].type == x86_const.X86_OP_REG and instr.old_instruction.operands[1].type == x86_const.X86_OP_IMM):
                print("ADDRESS DEL PRIMO ADD: ", hex(instr.old_instruction.address))
                str_instr = f"sub {instr.old_instruction.reg_name(instr.old_instruction.operands[0].reg)},{-instr.old_instruction.operands[1].imm}"
                asm, _ = self.ks.asm(str_instr, instr.old_instruction.address)
                bytes_arr = bytearray(asm)
                for i in self.cs.disasm(bytes_arr,instr.new_instruction.address):
                    print("vecchia istruzione: ", instr.old_instruction.mnemonic, instr.old_instruction.op_str)
                    print("nuova istruzione: ", i.mnemonic, i.op_str)
                    instr.new_instruction = i
                bytes_added += (len(bytes_arr) - len(instr.old_instruction.bytes))
                change_num += 1

            #substitute sub reg, x with add reg, -x
            elif (instr.old_instruction.id == x86_const.X86_INS_SUB and instr.old_instruction.operands[0].type == x86_const.X86_OP_REG and instr.old_instruction.operands[1].type == x86_const.X86_OP_IMM):
                print("ADDRESS DEL PRIMO SUB: ", hex(instr.old_instruction.address))
                str_instr = f"add {instr.old_instruction.reg_name(instr.old_instruction.operands[0].reg)},{-instr.old_instruction.operands[1].imm}"
                asm, _ = self.ks.asm(str_instr, instr.old_instruction.address)
                bytes_arr = bytearray(asm)
                for i in self.cs.disasm(bytes_arr,instr.new_instruction.address):
                    print("vecchia istruzione: ", instr.old_instruction.mnemonic, instr.old_instruction.op_str)
                    print("nuova istruzione: ", i.mnemonic, i.op_str)
                    instr.new_instruction = i
                bytes_added += (len(bytes_arr) - len(instr.old_instruction.bytes))
                change_num += 1

            #transform push r/m8/32 in (mov rax, r/m8/32; push rax)
            elif (self.push_mov == True and instr.old_instruction.id == x86_const.X86_INS_PUSH):
                if (instr.old_instruction.operands[0].type == x86_const.X86_OP_REG):
                    print("ADDRESS DEL PRIMO PUSH: ", hex(instr.old_instruction.address))
                    str_instr = f"mov rax,{instr.old_instruction.op_str}"
                    asm, _ = self.ks.asm(str_instr, instr.old_instruction.address)
                    bytes_arr = bytearray(asm)
                    for i in self.cs.disasm(bytes_arr,instr.new_instruction.address):
                        print("vecchia istruzione: ", instr.old_instruction.mnemonic, instr.old_instruction.op_str)
                        print("nuova istruzione: ", i.mnemonic, i.op_str)
                        instr.new_instruction = i
                    str_instr2 = f"push {instr.old_instruction.op_str}"
                    addr = instr.old_instruction.address + len(bytes_arr)
                    asm, _ = self.ks.asm(str_instr2, addr)
                    bytes_arr = bytearray(asm)
                    for i in self.cs.disasm(bytes_arr,addr):
                        insr = Instruction(i,i,None,None,None)
                        self.insert_instruction(num_instr + 1, insr)

                    bytes_added += (len(bytes_arr) - len(instr.old_instruction.bytes))
                    change_num += 1

            # trasforma inc reg in add reg,1
            elif (instr.old_instruction.id == x86_const.X86_INS_INC and instr.old_instruction.operands[0].type == x86_const.X86_OP_REG):
                print("ADDRESS DEL PRIMO INC: ", hex(instr.old_instruction.address))
                str_instr = f"add {instr.old_instruction.reg_name(instr.old_instruction.operands[0].reg)},1"
                asm, _ = self.ks.asm(str_instr, instr.old_instruction.address)
                bytes_arr = bytearray(asm)
                for i in self.cs.disasm(bytes_arr,instr.new_instruction.address):
                    print("vecchia istruzione: ", instr.old_instruction.mnemonic, instr.old_instruction.op_str)
                    print("nuova istruzione: ", i.mnemonic, i.op_str)
                    instr.new_instruction = i
                bytes_added += (len(bytes_arr) - len(instr.old_instruction.bytes))
                change_num += 1

            # trasforma dec reg in sub reg,1
            elif (instr.old_instruction.id == x86_const.X86_INS_DEC and instr.old_instruction.operands[0].type == x86_const.X86_OP_REG):
                print("ADDRESS DEL PRIMO DEC: ", hex(instr.old_instruction.address))
                str_instr = f"sub {instr.old_instruction.reg_name(instr.old_instruction.operands[0].reg)},1"
                asm, _ = self.ks.asm(str_instr, instr.old_instruction.address)
                bytes_arr = bytearray(asm)
                for i in self.cs.disasm(bytes_arr,instr.new_instruction.address):
                    print("vecchia istruzione: ", instr.old_instruction.mnemonic, instr.old_instruction.op_str)
                    print("nuova istruzione: ", i.mnemonic, i.op_str)
                    instr.new_instruction = i
                bytes_added += (len(bytes_arr) - len(instr.old_instruction.bytes))
                change_num += 1

            # trasforma and reg

        print("##########################################")
        print("BYTES ADDED: ",hex(bytes_added))
        print("##########################################")

    
    def write_strange_file(self,output_file):
        new_bytes = b''
        for x,i in enumerate(self.instructions):
            new_bytes += i.new_instruction.bytes

        padding1 = self.mem_address - len(new_bytes)
        # add 
        new_bytes += bytearray([0x90 for _ in range(padding1)])

        # create a bytearray of the instruction map
        map_bytes = b''
        for x,i in enumerate(self.instr_mapping):
            map_bytes += int(i[1]).to_bytes(4, byteorder='little', signed=True)

        new_bytes += map_bytes

        # extracted data lives after the PII instruction map
        if self.extracted_data:
            if not self.data_refs_finalized:
                self.finalize_data_refs()
            new_bytes += self.final_data_pad
            new_bytes += self.final_data_blob
        
        if output_file == None:
            output_file = 'new_payload.bin'

        # non modificare il file esistente, creano uno nuovo
        with open(output_file, 'wb') as f:
            f.seek(0)
            f.write(new_bytes)
    
    def write_file(self, output_file):
        new_bytes = b''
        for i in self.instructions:
            new_bytes += i.new_instruction.bytes

        # data extracted with --extract-data goes after the code
        if self.extracted_data:
            if not self.data_refs_finalized:
                self.finalize_data_refs()
            new_bytes += self.final_data_pad
            new_bytes += self.final_data_blob
        elif not self.morph_applied and len(new_bytes) == self.sweep_coverage:
            # Capstone skipdata can leave a tail un-disassembled: keep it when
            # the instruction stream was not modified.
            new_bytes += self.sweep_tail
        elif self.morph_applied and self.sweep_tail:
            print("WARNING: Capstone stopped before the end of the payload; "
                  "the untouched tail is not included after morphing. "
                  "Use --extract-data to rebuild the full payload.")

        # non modificare il file esistente, creano uno nuovo
        if output_file == None:
            output_file = 'new_payload.bin'
        with open(output_file, 'wb') as f:
            f.seek(0)
            f.write(new_bytes)


def print_usage():
    print("Usage: python pobf86.py <file> <options>")
    print("Options:")
    print("--help                                           Show  this help message and exit")
    print("--equal-instructions, -eq                        Modify instructions to make them equal")
    print("--bogus-cf, -bcf                                 Add bogus control flow instructions")
    print("--insert-nop, -nop                               Insert NOP instructions")
    print("--instruction-block-permutation, -ibp            Permute instruction blocks")
    print("--position-independent-instr, -pii               Indexed PII dispatcher (works with -xd)")
    print("--instruction-permutation, -ip                   Single-instruction permutation (works with -xd)")
    print("--find-data, -fd                                 Find data with symbolic exploration and exit")
    print("--extract-data, -xd                              Move data to the end of the payload and fix references")
    print("--extract-unknown, -xu                           Also move outside_cfg ranges (risky)")
    print("--eliminate-bad-instructions, -ebi               Expand loop/jecxz short branches")
    print("--data-timeout <seconds>                         Symbolic exploration timeout (default 120)")
    print("--data-cache <file>                              Data cache (default data_cache.json)")
    print("--no-data-cache, -nc                             Disable the data cache")
    print("--refresh-data-cache, -rc                        Ignore and replace the cached entry")
    print("--output,-o <file>                               Output file name")


def start(file=None):

    equal_instr = False
    bogus_cf = False
    insert_nop = False
    instruction_block_permutation = False
    position_independent_instr = False
    instruction_permutation = False
    find_data = False
    extract_data = False
    extract_unknown = False
    eliminate_bad = False
    data_timeout = 120.0
    data_cache = "data_cache.json"
    no_data_cache = False
    refresh_data_cache = False
    output_file = None

    if file == None:
        if len(sys.argv) < 2:
            print_usage()
            sys.exit(1)
        if sys.argv[1] == "--help" or "--help" in sys.argv[2:]:
            print_usage()
            sys.exit(0)
        zone = Zone(sys.argv[1])
    else:
        zone = Zone(file)

    opt_args = sys.argv[1:]
    for arg in opt_args:
        if arg == "--equal-instructions" or arg == "-eq":
            equal_instr = True
        elif arg == "--bogus-cf" or arg == "-bcf":
            bogus_cf = True
        elif arg == "--insert-nop" or arg == "-nop":
            insert_nop = True
        elif arg == "--instruction-block-permutation" or arg == "-ibp":
            instruction_block_permutation = True
        elif arg == "--position-independent-instr" or arg == "-pii":
            position_independent_instr = True
        elif arg == "--instruction-permutation" or arg == "-ip":
            instruction_permutation = True
        elif arg == "--find-data" or arg == "-fd":
            find_data = True
        elif arg == "--extract-data" or arg == "-xd":
            extract_data = True
        elif arg == "--extract-unknown" or arg == "-xu":
            extract_unknown = True
        elif (arg == "--eliminate-bad-instructions" or arg == "-ebi"
              or arg == "--eliminate-bad"):
            eliminate_bad = True
        elif arg == "--data-timeout":
            try:
                data_timeout = float(opt_args[opt_args.index(arg) + 1])
            except (IndexError, ValueError):
                print("--data-timeout requires a number of seconds")
                sys.exit(1)
        elif arg == "--data-cache":
            try:
                data_cache = opt_args[opt_args.index(arg) + 1]
            except IndexError:
                print("--data-cache requires a file name")
                sys.exit(1)
        elif arg == "--no-data-cache" or arg == "-nc":
            no_data_cache = True
        elif arg == "--refresh-data-cache" or arg == "-rc":
            refresh_data_cache = True
        elif arg == "--output" or arg == "-o":
            output_file = opt_args[opt_args.index(arg) + 1]

    if data_timeout < 0:
        print("--data-timeout must be nonnegative")
        sys.exit(1)

    if position_independent_instr and instruction_permutation:
        print("ERROR: -pii and -ip are different techniques; choose one")
        sys.exit(1)

    if extract_data and position_independent_instr:
        print("[pii] indexed dispatcher; data blob goes after the "
              "instruction map")

    if (position_independent_instr or instruction_permutation) and not eliminate_bad:
        print("[bad] enabling short-branch expansion for PII/permutation")
        eliminate_bad = True

    morph_requested = (equal_instr or instruction_block_permutation
                       or bogus_cf or insert_nop)
    if (morph_requested or eliminate_bad or position_independent_instr
            or instruction_permutation):
        zone.morph_applied = True

# INITIALIZATION / DATA EXTRACTION

    if find_data or extract_data:
        sections, xrefs = zone.analyze_data(
            timeout=data_timeout,
            print_strings=find_data,
            cache_path=data_cache,
            use_cache=not no_data_cache,
            refresh_cache=refresh_data_cache,
        )
        if find_data and not extract_data:
            print("Data analysis only; no payload written.")
            sys.exit(0)

        zone.extract_data(sections, xrefs, include_unknown=extract_unknown)

        try:
            zone.create_jmp_table()
        except Exception as e:
            print("create_jmp_table() skipped: ", e)
        if (morph_requested or eliminate_bad
                or instruction_permutation or position_independent_instr):
            zone.create_label_table()
        if eliminate_bad:
            zone.eliminate_bad_instructions()
        if morph_requested:
            if equal_instr == True:
                zone.equal_instructions()
            if instruction_block_permutation == True:
                zone.chaos_cf()
                zone.shuffle_blocks()
            if bogus_cf == True:
                zone.bogus_control_flow()
            if insert_nop == True:
                zone.insert_random_nop()
        if position_independent_instr:
            zone.pii_dispatcher_v2()
        elif instruction_permutation:
            zone.pii_permute_instructions()
            zone.update_label_table()
        elif morph_requested or eliminate_bad:
            zone.update_label_table()

        # the final layout is known only now: fill in the stub displacements
        zone.finalize_data_refs()
        zone.print_instructions()
        if position_independent_instr:
            zone.write_strange_file(output_file)
        else:
            zone.write_file(output_file)
        zone.print_instructions()
        print(f"Output: {output_file if output_file else 'new_payload.bin'}")
        print("FINE")
        return

# NORMAL PIPELINE

    if (morph_requested or eliminate_bad or position_independent_instr
            or instruction_permutation):
        try:
            zone.create_jmp_table()
        except Exception as e:
            print("create_jmp_table() skipped: ", e)
        zone.create_label_table()

    if equal_instr or insert_nop or bogus_cf:
        zone.mark_data_ranges32()

    if eliminate_bad:
        zone.eliminate_bad_instructions()

# CODE MODIFICATION
    if equal_instr == True:
        zone.equal_instructions()
    if instruction_block_permutation == True:
        zone.chaos_cf()
        zone.shuffle_blocks()
    if bogus_cf == True:
        zone.bogus_control_flow()
    if insert_nop == True:
        zone.insert_random_nop()

    if position_independent_instr == True:
        zone.pii_dispatcher_v2()
    elif instruction_permutation == True:
        zone.pii_permute_instructions()

    if (not position_independent_instr
            and (morph_requested or eliminate_bad or instruction_permutation)):
        zone.update_label_table()

    zone.print_blocks()
    zone.print_instructions()

# WRITE MODIFICATION
    if position_independent_instr == True:
        zone.write_strange_file(output_file)
    else:
        zone.write_file(output_file)
    zone.print_instructions()
    print("FINE")


if __name__ == "__main__":
    start()
