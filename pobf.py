from capstone import *   #e' un disassembler
from keystone import *   #e' un assembler
import sys
import pefile
import time
# import lief
import os
import json
import hashlib
import random
import re
from capstone import x86_const
import zone_utils
import increase_text
import traceback
# import asmjit
import subprocess
import symbolic_payload_coverage



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
        # set when this instruction is a rewritten reference to extracted data
        self.data_ref_fixup = None
        # set on trampoline short branches created by eliminate_bad_instructions
        self.bad_expanded = False




class Zone:

    # bump when the cached section format or the classification changes
    DATA_CACHE_SCHEMA = 1

    def __init__(self, file):


        # inizializzo il disassembler
        # initialize the disassembler
        self.cs = Cs(CS_ARCH_X86, CS_MODE_64)  #pip install capstone==5.0.0.post1 ONLY INSTALL THIS VERSION. ON OTHER VERSIONS IT DOES NOT WAR skipdataK
        self.cs.detail = True

        #utile per skippare dati inutili nella .text (tipo stringhe o tabelle di jump)
        # useful for skipping useless data in the .text (like strings or jump
        self.cs.skipdata = True 



        #list of registers 
        self.reg_list64 = ['rax','rbx','rcx','rdx','rsi','rdi','r8','r9','r10','r11','r12','r13','r14','r15']
        # self.reg_list32 = ['eax','ebx','ecx','edx','esi','edi','ebp','esp','r8d','r9d','r10d','r11d','r12d','r13d','r14d','r15d']
        self.reg_list32 = ['eax','ebx','ecx','edx','esi','edi']

        self.reg_list16 = ['ax','bx','cx','dx','si','di','bp','sp','r8w','r9w','r10w','r11w','r12w','r13w','r14w','r15w']
        self.reg_list8 = ['al','bl','cl','dl','sil','dil','bpl','spl','r8b','r9b','r10b','r11b','r12b','r13b','r14b','r15b']
        self.reg_list8h = ['ah','bh','ch','dh']
        self.reg_lists = [self.reg_list64,self.reg_list32,self.reg_list16,self.reg_list8,self.reg_list8h]

        # list of all the possible nop instructions
        self.no_ops_templates = ['nop','sub','add','mov','lea','push','or','xor','and','inc','sar','shr','shl','rcl','rcr', 'jmp']

        self.file = file

        # inizializzo l'assembler
        # initialize the assembler
        self.ks = Ks(KS_ARCH_X86, KS_MODE_64)
        
        self.push_mov = False

        # blocks for future implementation of bogus control flow
        self.instr_blocks = []
        self.block_size = 7


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

        #dizionario di istruzioni, molto utile dal punto di vista delle performance(tempo di accesso costante)
        #  dictionary of instructions, very useful from a performance point of view (constant access time)
        self.instr_dict = {}
        # ductionary like instr_dict but with key updated to the old_instruction(not the original)
        self.updated_instr_dict = {}

        self.payload_size = 0

        self.stub_address = 0
        self.stub_size = 0
        self.mem_address = 0
        self.counter_address = 0
        self.instr_mapping = []

        self.pii_enabled = False

        self.stub2_address = 0
        self.stub2_bytearr = 0
        self.stub2_size = 0

        self.init_address = 0
        self.wrap_instruction_num = 5

        self.bogus_probability = 20
        self.last_chosen_reg = None

        with open(self.file, "rb") as f:
            self.raw_code = f.read()
            f.close()

        self.do_not_touch = []

        # lunghezza del codice originale
        self.original_code_length = len(self.raw_code)
        self.equal_instructions_substitutions = 0
        self.base_address = 0

        self.nops_addedd = 0

        self.bytes_to_add = []

        self.data_xrefs = []
        self.data_sections = []

        # data-extraction state (opt-in, see --extract-data)
        self.extracted_data = []
        self.data_ref_fixups = []
        self.final_data_blob = None
        self.final_data_pad = b''
        self.final_code_len = 0
        self.data_refs_finalized = False
        self.data_analysis_done = False

        # assembly-wrapping state (opt-in, see --assembly-wrapping)
        self.final_payload_bytes = None
        self.layout_override = None
        self.code_length_override = 0


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
        self.morph_applied = False

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
                if (x86_const.X86_GRP_JUMP in instr.new_instruction.groups) or (x86_const.X86_GRP_CALL in instr.new_instruction.groups) or (instr.new_instruction.mnemonic == 'loop') or (instr.new_instruction.mnemonic == 'jrcxz'):
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

    # after every change in the instructions list, I have to update the instr_dict
    # the update is made simply by iterating over the instructions list and updating the instr_dict and updating addresses of instructions
    def update_instr(self):
        print("UPDATE INSTR")
        
        new_instr_dict = {}
        for x,i in enumerate(self.instructions):
            try:

                if x == 0:
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

        do_not_touch_instr = []

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
                    if entry[0] in do_not_touch_instr:
                        continue
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
                            if diff > 126:                                
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
        try:
            if index == 0:
                self.instructions[0].prev_instruction = instruction
                instruction.next_instruction = self.instructions[0]
                self.instructions.insert(0,instruction)
                return

            if index >= len(self.instructions):
                self.instructions[-1].next_instruction = instruction
                instruction.prev_instruction = self.instructions[-1]
                self.instructions.append(instruction)
                return            
            self.instructions[index - 1].next_instruction = instruction
            self.instructions[index].prev_instruction = instruction

            instruction.prev_instruction = self.instructions[index - 1]
            instruction.next_instruction = self.instructions[index]

            self.instructions.insert(index,instruction)
        except Exception as e:
            print("Errore in insert_instruction(): ",e)
            print("Indirizzo: ",hex(instruction.new_instruction.address))
            print("stringa: ",instruction.new_instruction.mnemonic + '  ' + instruction.new_instruction.op_str)
            print("index: ",index)
            
    def eliminate_instruction(self, index):
        self.instructions[index - 1].next_instruction = self.instructions[index + 1]
        self.instructions[index + 1].prev_instruction = self.instructions[index - 1]
        self.instructions.pop(index)
                

    def short_branch_spans(self):
        """(address, target) pairs of the nested loop/jcxz branches."""
        spans = []
        for scan_instr in self.instructions:
            mnemonic = scan_instr.new_instruction.mnemonic
            if mnemonic not in ('loop', 'loope', 'loopne',
                                'jrcxz', 'jecxz', 'jcxz'):
                continue
            target = zone_utils.estrai_valore(
                scan_instr.new_instruction.op_str)
            spans.append((scan_instr.new_instruction.address, target))
        return spans

    def inside_short_branch_span(self, point):
        """True when `point` sits between a short branch and its target."""
        for branch, target in self.short_branch_spans():
            if target > branch:
                if branch < point <= target:
                    return True
            else:
                if target <= point <= branch:
                    return True
        return False

    # function that randomly inserts some do-nothing operations
    def insert_random_nop(self):

        inserted_nops = 0
        # A short conditional branch (loop/jrcxz) has a signed 8-bit
        # displacement: inserting bytes between the branch and its target can
        # push it out of range. Leave those spans alone.
        short_branches = []
        for scan_instr in self.instructions:
            mnemonic = scan_instr.new_instruction.mnemonic
            if mnemonic not in ('loop', 'loope', 'loopne',
                                'jrcxz', 'jecxz', 'jcxz'):
                continue
            target = zone_utils.estrai_valore(
                scan_instr.new_instruction.op_str)
            short_branches.append((scan_instr.new_instruction.address, target))

        def breaks_short_branch(point):
            for branch, target in short_branches:
                if target > branch:
                    if branch < point <= target:
                        return True
                else:
                    if target <= point <= branch:
                        return True
            return False

        for num_instr,instr in enumerate(self.instructions):
            try:

                # if instr.new_instruction.address >= new_entry_point:
                #     break
                if instr.new_instruction.mnemonic == '.byte':
                    continue
                #checko che non sia dentro una jmp table della .text
                if self.check_if_inside_jmp_table(instr.original_instruction.address) == True:
                    continue

                if (instr.prev_instruction is not None
                        and instr.prev_instruction.new_instruction.mnemonic == 'pushf') \
                        or instr.new_instruction.mnemonic == 'pushf':
                    continue

                if breaks_short_branch(instr.new_instruction.address +
                                       instr.new_instruction.size):
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
                reg_list = None
                reg = None

                # just a random probability to insert a nop
                probability = random.randint(0,100)
                if probability <= 20:

                    # choose a random NOP operation
                    operazione = random.choice(self.no_ops_templates)
                    # choose a random number of NOPs to insert
                    nop_num = random.randint(1,2)

                    # choose a random register to do the nop
                    reg = random.choice(self.reg_list64)

# IMPORTANT : Why there is pushf; nop; popf in every instruction?
# BECAUSE even if these operations do nothing they still fuck up the CPU flags, therefore you need to save them and restore
# maybe this is bad solution because it can be easily signatured (?) 

                    if operazione == 'nop':
                        asm, _ = self.ks.asm('pushf;nop; popf', instr.new_instruction.address + instr.new_instruction.size)

                    if operazione == 'sub':
                        asm, _ = self.ks.asm(f'pushf;sub {reg},0x0; popf', instr.new_instruction.address + instr.new_instruction.size)
                    
                    if operazione == 'add':
                        asm, _ = self.ks.asm(f'pushf;add {reg},0x0; popf', instr.new_instruction.address + instr.new_instruction.size)
                    
                    if operazione == 'mov':
                        asm, _ = self.ks.asm(f'pushf;mov {reg},{reg}; popf', instr.new_instruction.address + instr.new_instruction.size)

                    if operazione == 'lea':
                        asm, _ = self.ks.asm(f'pushf;lea {reg},[{reg}+0]; popf', instr.new_instruction.address + instr.new_instruction.size)

                    if operazione == 'push':
                        nop_num = 1
                        asm, _ = self.ks.asm(f'pushf;push {reg}; pop {reg}; popf', instr.new_instruction.address + instr.new_instruction.size)


                    if operazione == 'inc':
                        nop_num = 1
                        asm, _ = self.ks.asm(f'pushf;dec {reg}; inc {reg}; popf', instr.new_instruction.address + instr.new_instruction.size)
                    
                    if operazione == 'sar':
                        asm, _ = self.ks.asm(f'pushf;sar {reg},0x0; popf', instr.new_instruction.address + instr.new_instruction.size)
                    
                    if operazione == 'shr':
                        asm, _ = self.ks.asm(f'pushf;shr {reg},0x0; popf', instr.new_instruction.address + instr.new_instruction.size)
                    
                    if operazione == 'shl':
                        asm, _ = self.ks.asm(f'pushf;shl {reg},0x0; popf', instr.new_instruction.address + instr.new_instruction.size)
                    
                    if operazione == 'rcl':
                        asm, _ = self.ks.asm(f'pushf;rcl {reg},0x0; popf', instr.new_instruction.address + instr.new_instruction.size)
                    
                    if operazione == 'rcr':
                        asm, _ = self.ks.asm(f'pushf;rcr {reg},0x0; popf', instr.new_instruction.address + instr.new_instruction.size)
                    
                    if operazione == 'xor':
                        asm, _ = self.ks.asm(f'pushf;xor {reg},0x0; popf', instr.new_instruction.address + instr.new_instruction.size)

                    if operazione == 'and':
                        asm, _ = self.ks.asm(f'pushf;and {reg},{reg}; popf', instr.new_instruction.address + instr.new_instruction.size)

                    
                    if operazione == 'or':
                        asm, _ = self.ks.asm(f'pushf;or {reg},{reg}; popf', instr.new_instruction.address + instr.new_instruction.size)
                    
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

                continue

    def chaos_cf(self):
        """Split instructions into blocks and add a jmp to the next block.

        The old implementation mutated the list while enumerating it, skipped
        the last instruction, and never appended the final block. This version
        builds the complete block list first: every block except the last ends
        with a jmp to the next block's first instruction. -ebi trampolines are
        kept inside one block.
        """
        old = list(self.instructions)
        self.instr_blocks = []
        index = 0
        while index < len(old):
            target_size = random.randint(5, 9)
            block = []
            while index < len(old) and len(block) < target_size:
                instr = old[index]
                block.append(instr)
                index += 1
                if instr.bad_expanded:
                    # keep the whole trampoline in this block
                    while index < len(old) and old[index].bad_expanded:
                        block.append(old[index])
                        index += 1
            self.instr_blocks.append(block)

        slots = []
        for block_index, block in enumerate(self.instr_blocks):
            slot = list(block)
            if block_index + 1 < len(self.instr_blocks):
                last = block[-1]
                address = (last.new_instruction.address
                           + last.new_instruction.size)
                asm, _ = self.ks.asm(f"jmp {address}", address)
                for capstone_instr in self.cs.disasm(bytes(asm), address):
                    jmp = Instruction(capstone_instr, capstone_instr,
                                      capstone_instr, None, None)
                    jmp.address_history.append(capstone_instr.address)
                    slot.append(jmp)
                    self.short_label_table.append(
                        (jmp, self.instr_blocks[block_index + 1][0]))
                    break
            slots.append(slot)

        self.instr_blocks = slots
        self.instructions = [instr for slot in slots for instr in slot]
        for x, instr in enumerate(self.instructions):
            instr.prev_instruction = (self.instructions[x - 1] if x > 0
                                      else None)
            instr.next_instruction = (self.instructions[x + 1]
                                      if x + 1 < len(self.instructions)
                                      else None)

    def shuffle_blocks(self):
        # Keep the entry block first and the original last block last: the
        # last block has no successor jmp, so it must not fall through into a
        # shuffled block. Only the middle blocks are shuffled.
        blocks = self.instr_blocks
        if len(blocks) > 2:
            middle = blocks[1:-1]
            random.shuffle(middle)
            blocks = [blocks[0]] + middle + [blocks[-1]]
        self.instr_blocks = blocks

        self.instructions = [instr for block in blocks for instr in block]
        for x, instr in enumerate(self.instructions):
            instr.prev_instruction = (self.instructions[x - 1] if x > 0
                                      else None)
            instr.next_instruction = (self.instructions[x + 1]
                                      if x + 1 < len(self.instructions)
                                      else None)


    def decode_original_at(self, address):
        """Decode one instruction from the original payload bytes at address."""
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

        The classic getpc idiom is ``call $+5; pop reg``, where the pop is the
        first instruction after the inline data.  Some Metasploit stagers use a
        *late pop* instead: the callee starts with normal code, pushes/pops a
        few temporary values, and only then consumes the saved return address::

            call inline_data_end      ; pushes inline_data_start
            <inline data>
        inline_data_end:
            mov rcx, rax
            push rbx
            pop rdx
            pop r8                    ; r8 = inline_data_start

        This helper starts with one item on the stack (the value pushed by the
        call) and walks instructions until a ``pop`` consumes it.  Returns
        ``(pop_insn, reg_name)`` or ``None``.  Branches, calls, returns and
        unknown rsp changes abort the simulation.
        """
        depth = 1  # the call pushed one 8-byte return address
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
                    if reg in self.reg_list64:
                        return insn, reg
                    return None
                depth -= 1
                if depth <= 0:
                    return None
            elif (mnemonic in ("sub", "add") and len(ops) >= 2
                  and ops[0].type == x86_const.X86_OP_REG
                  and insn.reg_name(ops[0].reg) == "rsp"
                  and ops[1].type == x86_const.X86_OP_IMM):
                slots = ops[1].imm // 8
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
        """
        Trova possibili riferimenti diretti alle sezioni dati.

        Istruzioni e sezioni devono usare lo stesso spazio di indirizzi.
        La lunghezza nella tupla è quella del candidato dati colpito.

        Oltre agli operandi espliciti (immediati e memoria RIP/assoluta),
        riconosce l'idioma position-independent ``call $+N; pop reg``: il call
        mette sullo stack l'indirizzo di ritorno, cioè il puntatore ai dati
        inline che seguono. Le istruzioni che iniziano dentro una sezione dati
        (le stringhe decodificate come codice dallo sweep lineare) vengono
        ignorate, e i target dei salti non sono trattati come puntatori.

        Con sections=None le sezioni sono cercate con
        symbolic_payload_coverage.find_data_sections(); analysis_kwargs sono
        passati a quella funzione (es. timeout=30, scan_all=True).
        """
        if sections is None:
            sections = symbolic_payload_coverage.find_data_sections(
                self.file,
                arch="x64",
                base_address=base_address,
                **analysis_kwargs,
            )

        # kept for extract_data()
        self.data_sections = sections

        ranges = []
        for section in sections:
            start = int(section["address"])
            length = int(section["length"])

            if length > 0:
                ranges.append((start, start + length))

        ranges.sort()

        mask64 = (1 << 64) - 1
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

        # Lo sweep lineare può aver decodificato i dati inline come istruzioni,
        # quindi il callee va decodificato direttamente dai byte originali.
        def decode_at(address):
            return self.decode_original_at(address)

        for entry in self.instructions:
            insn = entry.original_instruction

            # Capstone usa id=0 per i dati prodotti da skipdata.
            if insn.id == 0 or insn.mnemonic == ".byte":
                continue

            # Lo sweep lineare decodifica anche le stringhe come istruzioni:
            # quei byte sono dati e non devono generare riferimenti.
            if overlaps_data(insn):
                continue

            is_control_flow = (
                x86_const.X86_GRP_JUMP in insn.groups
                or x86_const.X86_GRP_CALL in insn.groups
                or x86_const.X86_GRP_BRANCH_RELATIVE in insn.groups
                or insn.mnemonic in (
                    "loop", "loope", "loopne", "jrcxz", "jecxz", "jcxz",
                )
            )

            # call $+N; pop reg (classic) oppure call $+N; ...; pop reg
            # (late pop): il call spinge l'indirizzo di ritorno, che è il
            # puntatore ai dati inline usato dallo shellcode position-independent.
            if include_getpc and insn.mnemonic == "call" and insn.operands:
                first = insn.operands[0]
                if first.type == x86_const.X86_OP_IMM:
                    return_address = (insn.address + insn.size) & mask64
                    callee = decode_at(first.imm & mask64)
                    span = containing_range(return_address)
                    if callee is not None:
                        if callee.mnemonic.startswith("pop"):
                            add_xref(insn.address, return_address)
                        elif (span is not None
                              and span[0] == return_address
                              and callee.address == span[1]):
                            # Late-pop getpc: the address is consumed by a pop
                            # placed after some stack-neutral instructions.
                            if self._simulate_getpc_consumer(callee.address):
                                add_xref(insn.address, return_address)

            for op in insn.operands:
                target = None

                if op.type == x86_const.X86_OP_IMM:
                    # I target di salti e chiamate sono indirizzi di codice,
                    # non puntatori a dati.
                    if (include_immediates and not is_control_flow
                            and insn.mnemonic.split()[0] in
                            ("mov", "movabs", "push")):
                        # È un candidato: un immediato non è sempre un puntatore.
                        target = op.imm & mask64

                elif op.type == x86_const.X86_OP_MEM:
                    mem = op.mem

                    # FS/GS richiedono la base del segmento a runtime.
                    # LEA calcola invece solo l'indirizzo effettivo.
                    if (
                        mem.segment in (
                            x86_const.X86_REG_FS,
                            x86_const.X86_REG_GS,
                        )
                        and insn.id != x86_const.X86_INS_LEA
                    ):
                        continue

                    # Un indice richiede di conoscere il valore del registro.
                    if mem.index != invalid:
                        continue

                    if mem.base == x86_const.X86_REG_RIP:
                        target = (
                            insn.address + insn.size + mem.disp
                        ) & mask64

                    elif mem.base == x86_const.X86_REG_EIP:
                        target = (
                            insn.address + insn.size + mem.disp
                        ) & 0xFFFFFFFF

                    elif mem.base == invalid:
                        # Memoria assoluta, senza registri base o indice.
                        address_mask = (1 << (insn.addr_size * 8)) - 1
                        target = mem.disp & address_mask

                if target is not None:
                    add_xref(insn.address, target)

        # Ricalcola i risultati senza accumulare duplicati tra chiamate.
        self.data_xrefs = xrefs
        return xrefs

    # ------------------------------------------------------------------
    # Data extraction (opt-in with --extract-data)
    #
    # The payload bytes are never renumbered: every data site is replaced by
    # a same-size `lea reg, [rip + disp]` + NOP padding, so create_label_table()
    # and update_label_table() keep working. The data is appended after the
    # code and the displacements are filled in only after the final layout is
    # known (i.e. after the optional morphing).
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

    def assemble_lea_rip(self, reg, displacement, address=0):
        """Assemble `lea reg, [rip + displacement]` (7 bytes)."""
        if displacement >= 0:
            text = f"lea {reg}, [rip + {displacement}]"
        else:
            text = f"lea {reg}, [rip - {-displacement}]"
        asm, _ = self.ks.asm(text, address)
        if not asm:
            raise RuntimeError(f"cannot assemble {text}")
        raw = bytes(asm)
        if len(raw) != 7:
            raise RuntimeError(f"unexpected size {len(raw)} for {text}")
        return raw

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
            "arch": "x64",
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
        """Run (or reuse) the symbolic data discovery.

        The sections are cached in a JSON file keyed by the SHA-256 of the
        payload. Xrefs are cheap and are always recomputed against the current
        instruction list. Use refresh_cache=True to bypass and replace the
        stored entry, use_cache=False to disable reading and writing.
        """
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
                arch="x64",
                base_address=0,
                timeout=timeout,
                print_strings=print_strings,
            )
            if use_cache:
                self._save_data_cache(cache_path, payload_hash, sections,
                                      timeout)

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

    def _data_preview(self, section):
        raw = section["bytes"]
        try:
            if section.get("kind") == "ascii":
                return raw[:-1].decode("ascii")
            if section.get("kind") == "utf16le":
                return raw[:-2].decode("utf-16le")
        except UnicodeDecodeError:
            pass
        return raw[:24].hex(" ")

    def _classify_data_ref(self, source, target, section_start, section_length):
        """Classify one xref as getpc/rip/abs/imm or unsupported."""
        entry = self.instr_dict.get(source)
        if entry is None:
            return {"kind": "unsupported", "source": source,
                    "reason": "no instruction at source"}
        insn = entry.original_instruction
        mask64 = (1 << 64) - 1
        invalid = x86_const.X86_REG_INVALID
        delta = target - section_start

        if insn.mnemonic == "call" and insn.operands and \
                insn.operands[0].type == x86_const.X86_OP_IMM:
            if target == source + insn.size and delta == 0:
                callee = self.decode_original_at(insn.operands[0].imm & mask64)
                if (callee is not None and callee.mnemonic == "pop"
                        and callee.operands
                        and callee.operands[0].type == x86_const.X86_OP_REG):
                    reg = callee.reg_name(callee.operands[0].reg)
                    if reg in self.reg_list64 and \
                            callee.address == section_start + section_length:
                        return {
                            "kind": "getpc", "source": source, "instr": entry,
                            "reg": reg, "delta": 0,
                            "region_start": source,
                            "region_end": callee.address + callee.size,
                            "old_target": target,
                        }
                if (callee is not None
                        and callee.address == section_start + section_length):
                    # Late pop: the pushed address is consumed after some
                    # stack-neutral instructions (see _simulate_getpc_consumer).
                    consumer = self._simulate_getpc_consumer(callee.address)
                    if consumer is not None:
                        pop_insn, reg = consumer
                        return {
                            "kind": "getpc_stub", "source": source,
                            "instr": entry, "reg": reg, "delta": 0,
                            "region_start": source,
                            "region_end": section_start + section_length,
                            "consumer": pop_insn,
                            "callee": callee.address,
                            "old_target": target,
                        }
            return {"kind": "unsupported", "source": source,
                    "reason": "call does not match a getpc data site"}

        for op_index, op in enumerate(insn.operands):
            if op.type == x86_const.X86_OP_MEM:
                mem = op.mem
                if mem.segment in (x86_const.X86_REG_FS, x86_const.X86_REG_GS):
                    continue
                if mem.index != invalid:
                    continue
                if mem.base == x86_const.X86_REG_RIP:
                    if insn.address + insn.size + mem.disp == target:
                        return {"kind": "rip", "source": source, "instr": entry,
                                "op_index": op_index, "delta": delta,
                                "old_disp": mem.disp, "old_target": target}
                elif mem.base == invalid:
                    address_mask = (1 << (insn.addr_size * 8)) - 1
                    if (mem.disp & address_mask) == target:
                        return {"kind": "abs", "source": source, "instr": entry,
                                "op_index": op_index, "delta": delta,
                                "old_disp": mem.disp, "old_target": target}
            elif op.type == x86_const.X86_OP_IMM:
                # Only instructions that can materialize an address. A
                # `cmp reg, 0x20b` constant is not a pointer.
                if insn.mnemonic.split()[0] not in ("mov", "movabs", "push"):
                    continue
                if (op.imm & mask64) == target:
                    return {"kind": "imm", "source": source, "instr": entry,
                            "op_index": op_index, "delta": delta,
                            "old_imm": op.imm & mask64, "old_target": target}

        return {"kind": "unsupported", "source": source,
                "reason": "no supported operand references the data"}

    def extract_data(self, sections=None, xrefs=None, *, include_unknown=False,
                     timeout=120):
        """Move discovered data to the end of the payload.

        Every `call $+N; pop reg` that pushes a data address becomes
        `lea reg, [rip + disp]` + NOPs (same byte length). Other supported
        references (RIP-relative, absolute memory, mov/push immediates) are
        recorded and patched by finalize_data_refs() once the final layout is
        known. Sections with references that cannot be rewritten safely are
        left in place and reported.
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
                min_size = 7 if ref["kind"] == "getpc" else 5
                if ref["region_end"] - ref["region_start"] < min_size:
                    print(f"[extract] keep {item['offset']:#x}: getpc region too small")
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
                if ref["kind"] == "getpc_stub":
                    # The call stays in place during extraction; finalize()
                    # replaces it with a jmp to a 5-byte stub placed just
                    # before the moved data.  Only the inline data is NOPed.
                    tail = ref["region_start"] + 5
                else:
                    lea = self.assemble_lea_rip(ref["reg"], 0, ref["region_start"])
                    new_code[ref["region_start"]:ref["region_start"] + len(lea)] = lea
                    tail = ref["region_start"] + len(lea)
                for offset in range(tail, ref["region_end"]):
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
                fixup = {"kind": ref["kind"], "section": index,
                         "source": ref["source"],
                         "delta": ref["delta"]}
                if ref["kind"] == "getpc":
                    instr = self.instr_dict.get(ref["region_start"])
                    if instr is None or instr.new_instruction.mnemonic != "lea" \
                            or instr.new_instruction.size != 7:
                        raise RuntimeError(
                            f"getpc rewrite at {ref['region_start']:#x} "
                            "did not produce a 7-byte lea")
                    fixup["instr"] = instr
                    fixup["reg"] = ref["reg"]
                elif ref["kind"] == "getpc_stub":
                    instr = self.instr_dict.get(ref["region_start"])
                    if instr is None or instr.new_instruction.mnemonic != "call" \
                            or instr.new_instruction.size != 5:
                        raise RuntimeError(
                            f"getpc rewrite at {ref['region_start']:#x} "
                            "did not keep a 5-byte call")
                    fixup = {"kind": "getpc_stub", "section": index,
                             "source": ref["source"], "delta": 0,
                             "instr": instr,
                             "callee": ref["callee"],
                             "old_target": ref["old_target"]}
                else:
                    instr = self.instr_dict.get(ref["source"])
                    if instr is None:
                        raise RuntimeError(
                            f"instruction at {ref['source']:#x} disappeared")
                    self._check_rebuilt_reference(instr.new_instruction, ref)
                    fixup["instr"] = instr
                    fixup["op_index"] = ref["op_index"]
                    fixup["old_disp"] = ref.get("old_disp")
                    fixup["old_imm"] = ref.get("old_imm")
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
        if kind == "rip":
            mem = insn.operands[ref["op_index"]].mem
            actual = insn.address + insn.size + mem.disp
        elif kind == "abs":
            mem = insn.operands[ref["op_index"]].mem
            address_mask = (1 << (insn.addr_size * 8)) - 1
            actual = mem.disp & address_mask
        elif kind == "imm":
            actual = insn.operands[ref["op_index"]].imm & ((1 << 64) - 1)
        else:
            raise RuntimeError(f"unknown reference kind {kind}")
        if actual != ref["old_target"]:
            raise RuntimeError(
                f"reference at {ref['source']:#x} changed during the rewrite")

    @staticmethod
    def _replace_first_hex(text, value):
        # Capstone prints small displacements in decimal (`[rip + 6]`) and
        # larger ones in hex (`[rip + 0x5f]`); accept both.
        match = re.search(r"0x[0-9a-fA-F]+|\b\d+\b", text)
        if match is None:
            return None
        return f"{text[:match.start()]}{hex(value)}{text[match.end():]}"

    def _patch_memory_reference(self, instr, insn_address, fixup, target):
        insn = instr.new_instruction
        kind = fixup["kind"]
        if kind == "rip":
            new_disp = target - (insn_address + insn.size)
            op_str = insn.op_str.replace("rip -", "rip +", 1)
            op_str = self._replace_first_hex(op_str, abs(new_disp))
            if new_disp < 0:
                op_str = op_str.replace("rip +", "rip -", 1)
        else:  # absolute memory operand
            new_disp = target
            op_str = self._replace_first_hex(insn.op_str, new_disp)
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
        if kind == "getpc":
            if (insn.mnemonic != "lea" or len(insn.operands) < 2
                    or insn.operands[1].type != x86_const.X86_OP_MEM):
                raise RuntimeError(
                    f"getpc rewrite at {fixup['source']:#x} is not a lea")
            mem = insn.operands[1].mem
            if mem.base != x86_const.X86_REG_RIP:
                raise RuntimeError(
                    f"getpc rewrite at {fixup['source']:#x} is not RIP-relative")
            if insn.reg_name(insn.operands[0].reg) != fixup["reg"]:
                raise RuntimeError(
                    f"getpc rewrite at {fixup['source']:#x} uses the wrong register")
            actual = insn_address + insn.size + mem.disp
        elif kind == "rip":
            actual = insn_address + insn.size + \
                insn.operands[fixup["op_index"]].mem.disp
        elif kind == "abs":
            mem = insn.operands[fixup["op_index"]].mem
            address_mask = (1 << (insn.addr_size * 8)) - 1
            actual = mem.disp & address_mask
        elif kind == "imm":
            actual = insn.operands[fixup["op_index"]].imm & ((1 << 64) - 1)
        else:
            raise RuntimeError(f"unknown fixup kind {kind}")
        if actual != target:
            raise RuntimeError(
                f"reference {fixup['source']:#x} points at {actual:#x} "
                f"instead of {target:#x}")

    def finalize_data_refs(self):
        """Lay out the extracted data and rewrite every reference.

        Must be called after the last morphing step: the final instruction
        addresses determine the RIP-relative displacement of each reference.
        """
        if not self.extracted_data:
            return
        if self.data_refs_finalized:
            return

        addresses = {}
        if self.layout_override is not None:
            # a layout pass (assembly wrapping) already decided where every
            # instruction lives and how long the code area is
            addresses = dict(self.layout_override)
            code_length = self.code_length_override
        else:
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
            # self.mem_address; the data blob goes after the map.
            map_start = self.mem_address
            map_size = 8 * len(self.instr_mapping)
            data_base = map_start + map_size
            pad = (-data_base) % 16
            data_start = data_base + pad
        else:
            data_start = code_length + ((-code_length) % 16)
            pad = data_start - code_length

        by_original = {instr.original_instruction.address: instr
                       for instr in self.instructions}
        stub_indices = {fixup["section"] for fixup in self.data_ref_fixups
                        if fixup["kind"] == "getpc_stub"}

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
                displacement = target - (insn_address + 7)
                raw = self.assemble_lea_rip(fixup["reg"], displacement,
                                            insn_address)
                new_instruction = next(
                    self.cs.disasm(raw, insn_address, count=1), None)
                if new_instruction is None:
                    raise RuntimeError(
                        f"cannot decode the getpc lea at {insn_address:#x}")
                instr.new_instruction = new_instruction
                instr.new_bytes = raw
            elif fixup["kind"] == "getpc_stub":
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
                        & ((1 << 64) - 1)) != stub_addr:
                    raise RuntimeError("getpc jmp target mismatch")
                if stub_addr + 5 != section["new_address"]:
                    raise RuntimeError("getpc stub is not adjacent to data")
                continue
            elif fixup["kind"] in ("rip", "abs"):
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
            map_size = 8 * len(self.instr_mapping)
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
                        
                        stringa = f"pushf;dec rcx;jne {hex(addr)};popf;"
                        asm, _ = self.ks.asm(stringa, instr.new_instruction.address)
                        bytes_arr = bytearray(asm)
                        for n,i in enumerate(self.cs.disasm(bytes_arr,instr.new_instruction.address)):
                            new_instr = Instruction(i,i,i,None,None)
                            self.insert_instruction(x+n,new_instr)
                            if i.mnemonic == 'jne':
                                self.short_label_table.append((new_instr,self.instr_dict[addr]))

                        
                        pointed_instr = self.instr_dict[addr]
                        pointed_instr_str = f"pushf;popf;{pointed_instr.new_instruction.mnemonic} {pointed_instr.new_instruction.op_str}"

                        pointed_instr_index = self.instructions.index(pointed_instr)
                        asm, _ = self.ks.asm(pointed_instr_str, pointed_instr.new_instruction.address)
                        bytes_arr = bytearray(asm)

                        # self.eliminate_instruction(pointed_instr_index)
                        old_addr = pointed_instr.new_instruction.address
                        for n,i in enumerate(self.cs.disasm(bytes_arr,pointed_instr.new_instruction.address)):
                            if n == 1:
                                pointed_instr.new_instruction = i
                                continue
                            new_instr = Instruction(i,i,i,None,None)
                            self.insert_instruction(pointed_instr_index+n,new_instr)
                            if i.mnemonic == 'jmp':
                                self.short_label_table.append((new_instr,self.instructions[pointed_instr_index + n + 1]))
                    # # readjust the je
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
                    print("TROVATO JRCXZ")
                    addr = zone_utils.estrai_valore(instr.new_instruction.op_str)

                    self.eliminate_instruction(x)

                    stringa = f"pushf;cmp rcx, 0x0;je {addr};popf"
                    asm, _ = self.ks.asm(stringa, instr.new_instruction.address)
                    bytes_arr = bytearray(asm)
                    for n,i in enumerate(self.cs.disasm(bytes_arr,instr.new_instruction.address)):
                        
                        new_instr = Instruction(i,i,i,None,None)
                        self.insert_instruction(x+n,new_instr)
                        if i.mnemonic == 'je':
                            self.short_label_table.append((new_instr,self.instr_dict[addr]))
                    # modifica l'istruzione jmp che punta a jrcxz

                    pointed_instr = self.instr_dict[addr]
                    pointed_instr_str = f"jmp {pointed_instr.new_instruction.address + 2 + 2 + 2};pushf;popf;{pointed_instr.new_instruction.mnemonic} {pointed_instr.new_instruction.op_str}"

                    pointed_instr_index = self.instructions.index(pointed_instr)
                    asm, _ = self.ks.asm(pointed_instr_str, pointed_instr.new_instruction.address)
                    bytes_arr = bytearray(asm)

                    # self.eliminate_instruction(pointed_instr_index)
                    old_addr = pointed_instr.new_instruction.address
                    for n,i in enumerate(self.cs.disasm(bytes_arr,pointed_instr.new_instruction.address)):
                        if n == 2:
                            pointed_instr.new_instruction = i
                            continue
                        new_instr = Instruction(i,i,i,None,None)
                        self.insert_instruction(pointed_instr_index+n,new_instr)
                        if i.mnemonic == 'jmp':
                            self.short_label_table.append((new_instr,self.instructions[pointed_instr_index + n + 1]))
                    # readjust the je
                    restart = True
                    # break


    def eliminate_bad_instructions(self):
        """Expand jrcxz/loop-family short branches into a 12-byte trampoline.

        Original:
            A: jrcxz target

        becomes:
            A+0:  jrcxz A+7        ; local +5, always in rel8 range
            A+2:  jmp fallthrough  ; near jmp, padded by update_label_table
            A+7:  jmp target
            A+12: fallthrough

        The two near jumps and the local jrcxz are registered in
        short_label_table; update_label_table() patches them to the final
        addresses. The local jrcxz never needs the 120-byte restart path.

        This runs after create_label_table() and before morphing. It handles
        jrcxz, jecxz, jcxz, loop, loope, loopne. Returns the number of expanded
        branches.
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
                    # this is the local +5 branch of a trampoline we created
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

                # jrcxz/loop at A, jmp A+12 at A+2, jmp target at A+7.
                # rel32 placeholders are patched by update_label_table().
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

                # drop the old label for this branch
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

                # local jrcxz -> second jmp; fallthrough jmp; target jmp
                self.short_label_table.append(
                    (sequence_instrs[0], sequence_instrs[2]))
                self.short_label_table.append(
                    (sequence_instrs[1], fallthrough))
                self.short_label_table.append(
                    (sequence_instrs[2], target_instr))

                # branches that pointed at the old instruction now enter the
                # trampoline head
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


    def check_unused_registers(self):
        unused_regs = []
        for reg in self.reg_list64:
            unused_regs.append(reg)
        
        for instr in self.instructions:
            instr_str = f"{instr.new_instruction.mnemonic} {instr.new_instruction.op_str}"
            for reg in self.reg_list64:
                if reg in instr_str:
                    if reg in unused_regs:
                        unused_regs.remove(reg)
        print("UNUSED REGISTERS: ",unused_regs)

        # DEBUG PURPOSE
        unused_regs = []


        if len(unused_regs) == 0:
            print("NO UNUSED REGISTERS, using rbp")
            unused_regs.append('rbp')
        return unused_regs
    def estimate_stub_address(self):
        original_size = 0
        instruction_num = 0
        for instr in self.instructions:
            original_size += len(instr.new_instruction.bytes)
            instruction_num += 1

        probable_addr = original_size + (1 + 5 + 5 + 5) * instruction_num    
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
                        asm1 = "pop rax"
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
                    new_str = f"pop rax;lea rsp, [rsp + 8];{instr.new_instruction.mnemonic} {instr.new_instruction.op_str};push {hex(0x3e8 + counter)};jmp {hex(self.stub_address)}"
                    
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
        push rax;
        push rcx;
        mov rcx, [rsp + 0x10]
        pushf;
        sub rcx, 0x3e8;
        inc rcx;
        mov rax, [rip + 0x25];
        mov rcx, [rax + 0x1000 - 5 + rcx * 8];
        sub rcx, 0x5
        add rax, rcx
        popf;
        pop rcx;
        jmp rax;
        '''
        asm, _ = self.ks.asm(stub_str,self.stub_address)
        bytes_arr = bytearray(asm)
        return len(bytes_arr)     

    def estimate_stub2_size(self):
        stub2_str = f'''
        pop r11;
        mov [r11 - 5 + 0x1000], r11;
        push r11;
        jmp r11;
        '''
        asm, _ = self.ks.asm(stub2_str,self.stub_address)
        bytes_arr = bytearray(asm)
        return len(bytes_arr)


    def shuffle_brain_blocks(self):
        counter = 0

        blocks = []
        block = []

        # jmp_blocks = []

        for x,instr in enumerate(self.instructions):

            if instr.new_instruction.mnemonic == 'pop' and instr.new_instruction.op_str == 'rax':
                if instr.next_instruction.new_instruction.mnemonic == "lea":
                    block.append(instr)
                    continue
            if x == len(self.instructions) - 1:
                block.append(instr)
                blocks.append(block)
                block = []
                continue
            if instr.new_instruction.mnemonic == 'jmp' and instr.next_instruction.new_instruction.mnemonic == 'pop' and instr.next_instruction.new_instruction.op_str == 'rax':
                block.append(instr)
                blocks.append(block)
                block = []
                continue
            block.append(instr)

        firstBlock = blocks[0]
        blocks = blocks[1:]




        random.shuffle(blocks)

        
        print("Blocks shuffled correctly ")



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
            if instr.new_instruction.mnemonic == "pop" and instr.new_instruction.op_str == "rax" and instr.next_instruction.new_instruction.mnemonic == "lea":#x % self.wrap_instruction_num == 1:
                
                self.instr_mapping.append((x,instr.new_instruction.address))
            instruction_num += 1

        for x,instr in enumerate(self.instructions):
            index  = 0
            if x == 0:
                continue
            if instr.new_instruction.mnemonic == "pop" and instr.new_instruction.op_str == "rax" and x % self.wrap_instruction_num == 1:
                for instr2 in self.instructions[x:x+5]:
                    if instr2.new_instruction.mnemonic == "push" and instr2.next_instruction.new_instruction.mnemonic == "jmp":
                        # print("push found")
                        index = int(instr2.new_instruction.op_str,16) - 0x3e8
                        # print("index: ",index)
                        try:
                            self.instr_mapping[index] = (index,instr.new_instruction.address)
                        except Exception as e:
                            print("self.instr_mapping: ",self.instr_mapping)
                            print("Errore in brain_obfuscator(): ",e)
                            print("index: ",index)
                            print("instr2: ",instr2.new_instruction.mnemonic + '  ' + instr2.new_instruction.op_str)
                            print("instr: ",instr.new_instruction.mnemonic + '  ' + instr.new_instruction.op_str)
                            traceback.print_exc()
                            continue
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


        init_addr_offset = self.init_address - (self.stub_address + 0x1a) 
        print("INIT ADDR OFFSET: ",init_addr_offset)    

        stub_str = f'''
        push rax;
        push rcx;
        mov rcx, [rsp + 0x10]
        pushf;
        sub rcx, 0x3e8;
        inc rcx;
        mov rax, [rip + {init_addr_offset}];
        mov rcx, [rax + {self.mem_address} - 5 + rcx * 8];
        sub rcx, 0x5
        add rax, rcx
        popf;
        pop rcx;
        jmp rax;
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

    def _pii_single_insn(self, text, address=0):
        asm, _ = self.ks.asm(text, address)
        for capstone_instr in self.cs.disasm(bytes(asm), address):
            instr = Instruction(capstone_instr, capstone_instr,
                                capstone_instr, None, None)
            instr.address_history.append(capstone_instr.address)
            return instr
        return None

    def _pii_scratch_register(self, instructions):
        used = " ".join(
            f"{instr.new_instruction.mnemonic} {instr.new_instruction.op_str}"
            for instr in instructions)
        for reg in self.reg_list64:
            if reg in ("rsp", "rbp"):
                continue
            if reg not in used:
                return reg
        print("WARNING: no unused PII scratch register; using r11")
        return "r11"

    def _pii_stub_text(self, map_displacement, scratch):
        # Save the registers the dispatcher uses, pop the handler index,
        # load the handler offset from the map, add the map's runtime
        # address, restore registers and flags, then jump through scratch.
        # The scratch register is chosen from registers unused by the payload.
        return ("push rax; push rcx; push rdx; "
                "mov rcx, [rsp + 24]; sub rcx, 0x3e8; "
                f"lea rax, [rip + {map_displacement}]; "
                "mov rdx, [rax + rcx * 8]; add rax, rdx; "
                f"mov {scratch}, rax; "
                "pop rdx; pop rcx; pop rax; add rsp, 8; popfq; "
                f"jmp {scratch}")

    def pii_dispatcher_v2(self):
        """Indexed dispatcher compatible with calls, returns and branches.

        Each instruction (or -ebi trampoline group) becomes a handler:
            <original instruction(s)>
            pushfq
            push 0x3e8 + next_index
            jmp stub

        The entry handler stays first; the remaining handler units are
        shuffled. A direct branch/call target is the handler start, so
        branches and calls need no special stack protocol. The stub pops the
        index, looks up the handler offset in a map, and jumps there. The map
        is placed after the code; extracted data is placed after the map.
        """
        if not self.instructions:
            return

        old = list(self.instructions)
        scratch = self._pii_scratch_register(old)
        address_to_instr = {
            instr.new_instruction.address: instr for instr in old
        }
        custom_getpc = {}
        for index, instr in enumerate(old):
            if instr.new_instruction.mnemonic != "call":
                continue
            operands = instr.new_instruction.operands
            if not operands or operands[0].type != x86_const.X86_OP_IMM:
                continue
            target = address_to_instr.get(operands[0].imm)
            if target is None:
                continue
            if target.new_instruction.mnemonic != "pop":
                continue
            fallthrough = (old[index + 1] if index + 1 < len(old)
                           else None)
            # Adjacent call/pop is a normal getpc, handled by extraction.
            if fallthrough is None or target is fallthrough:
                continue
            after_pop = target.next_instruction
            if after_pop is None or after_pop not in old:
                continue
            custom_getpc[instr] = (target.new_instruction.op_str,
                                   fallthrough, after_pop)

        terminator = self._pii_single_insn("ret", 0)
        getpc_fixups = []

        # Rewrite remote call/pop getpc first: the call becomes a lea to the
        # handler for its fallthrough, and dispatch continues after the pop.
        for instr, (reg, fallthrough, after_pop) in custom_getpc.items():
            lea = self._pii_single_insn(f"lea {reg}, [rip + 0]", 0)
            instr.new_instruction = lea.new_instruction
            getpc_fixups.append((instr, reg, fallthrough))

        # A normal instruction is one unit; an -ebi trampoline is one unit so
        # its local jrcxz/loop branch stays local after the shuffle.
        groups = []
        index = 0
        while index < len(old):
            group = [old[index]]
            if old[index].bad_expanded:
                cursor = index + 1
                while cursor < len(old) and old[cursor].bad_expanded:
                    group.append(old[cursor])
                    cursor += 1
                index = cursor
            else:
                index += 1
            groups.append(group)

        instr_unit = {}
        for unit_index, group in enumerate(groups):
            for instr in group:
                instr_unit[id(instr)] = unit_index

        records = []
        for unit_index, group in enumerate(groups):
            if len(group) == 1 and group[0] in custom_getpc:
                after_pop = custom_getpc[group[0]][2]
                next_index = instr_unit[id(after_pop)]
            else:
                next_index = (unit_index + 1
                              if unit_index + 1 < len(groups)
                              else len(groups))
            records.append((unit_index, group, next_index))

        # Keep the entry unit at offset 0; shuffle the rest.
        first = records[0]
        rest = records[1:]
        random.shuffle(rest)
        ordered = [first] + rest

        handlers = []
        stub_jumps = []
        for unit_index, group, next_index in ordered:
            handlers.extend(group)
            flags = self._pii_single_insn("pushfq", 0)
            push = self._pii_single_insn(f"push {0x3e8 + next_index}", 0)
            jump = self._pii_single_insn("jmp 0", 0)
            handlers.extend([flags, push, jump])
            stub_jumps.append(jump)
        handlers.append(terminator)

        stub_addr_guess = sum(len(x.new_instruction.bytes) for x in handlers)
        stub_placeholder = []
        asm, _ = self.ks.asm(self._pii_stub_text(0, scratch), stub_addr_guess)
        for capstone_instr in self.cs.disasm(bytes(asm), stub_addr_guess):
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

        for instr, reg, fallthrough in getpc_fixups:
            addr = addresses[id(instr)]
            target = addresses[id(fallthrough)]
            displacement = target - (addr + 7)
            asm, _ = self.ks.asm(f"lea {reg}, [rip + {displacement}]", addr)
            for capstone_instr in self.cs.disasm(bytes(asm), addr):
                instr.new_instruction = capstone_instr
                break

        stub_addr = addresses[id(stub_placeholder[0])]
        stub_size = sum(len(x.new_instruction.bytes)
                        for x in stub_placeholder)
        map_addr = stub_addr + stub_size

        # Reassemble the stub with the real map address. The lea uses a
        # disp32, so the instruction count/size does not change.
        lea_instr = next(x for x in stub_placeholder
                         if x.new_instruction.mnemonic == "lea")
        lea_next = (lea_instr.new_instruction.address
                    + lea_instr.new_instruction.size)
        map_displacement = map_addr - lea_next
        asm, _ = self.ks.asm(self._pii_stub_text(map_displacement, scratch),
                             stub_addr)
        new_stub = list(self.cs.disasm(bytes(asm), stub_addr))
        if len(new_stub) != len(stub_placeholder):
            raise RuntimeError("PII stub size changed during layout")
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
        print(f"[pii-v2] {len(records)} units, map at {map_addr:#x}, "
              f"{len(entries)} entries, shuffled")

    def pii_permute_instructions(self):
        """Position-independent instruction permutation.

        Each original instruction is paired with a jmp to its logical
        successor. The entry slot stays first; the remaining slots are
        shuffled. Because every fall-through becomes an explicit jmp, and
        every direct branch/call target is an Instruction object, the existing
        label table can repatch all control transfers after the shuffle.
        Calls and returns keep working because the CPU return address is the
        inserted jmp, which then dispatches to the logical successor.
        """
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
            if original[index].bad_expanded:
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

        print(f"[pii] permuted {len(original)} instructions into "
              f"{len(self.instructions)} slots")
        return len(self.instructions)

    def generate_assembly_tautology(self):
    # List of common registers (excluding esp/ebp for simplicity)
        # registers = random.choice(self.reg_list32)
        # print("REGISTERS: ",registers)
        # choose between 32 and 64 bit registers
        # reg_list = random.choice([self.reg_list32,self.reg_list64])
        reg = random.choice(self.reg_list64)
        while True:
            if reg != self.last_chosen_reg:
                break
            reg = random.choice(self.reg_list64)
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
            code = f"pushf;push {reg};mov {reg}, {imm};cmp {reg}, {imm};pop {reg};popf"
        elif pattern == 2:
            # Pattern 2: cmp reg, reg
            code = f"pushf;cmp {reg}, {reg};popf"
        elif pattern == 3:
            # Pattern 3: mov reg, imm; add reg, 0; cmp reg, imm
            code = f"pushf;push {reg};mov {reg}, {imm};add {reg}, 0;cmp {reg}, {imm}; pop {reg};popf"
        elif pattern == 4:
            # Pattern 4: mov reg, imm; sub reg, 0; cmp reg, imm
            code = f"pushf;push {reg};mov {reg}, {imm};sub {reg}, 0;cmp {reg}, {imm}; pop {reg};popf"
        elif pattern == 5:
            # Pattern 5: push imm; pop reg; cmp reg, imm
            code = f"pushf;push {reg};push {imm};pop {reg};cmp {reg}, {imm}; pop {reg};popf"
        elif pattern == 6:
            # Pattern 6: sub reg, reg; cmp reg, 0
            code = f"pushf;push {reg};sub {reg}, {reg};cmp {reg}, 0; pop {reg};popf"
        elif pattern == 7:
            # Pattern 7: xor reg, reg; cmp reg, 0
            code = f"pushf;push {reg}; xor {reg}, {reg};cmp {reg}, 0; pop {reg};popf"
        elif pattern == 8:
            # Pattern 9: mov reg, imm; neg reg; neg reg; cmp reg, imm
            code = f"pushf;push {reg}; mov {reg}, {imm};neg {reg};neg {reg};cmp {reg}, {imm}; pop {reg};popf"
        elif pattern == 9:
            # Pattern 10: mov reg, imm; or reg, 0; cmp reg, imm
            code = f"pushf;push {reg}; mov {reg}, {imm};or {reg}, 0;cmp {reg}, {imm}; pop {reg};popf"
        elif pattern == 10:
            # Pattern 11: mov reg, imm; and reg, 0xFFFFFFFF; cmp reg, imm
            code = f"pushf;push {reg};mov {reg}, {imm};and {reg}, 0xffffffffffffffff;cmp {reg}, {imm}; pop {reg};popf"
        elif pattern == 11:
            # Pattern 12: mov reg, imm; lea reg, [{reg}+0]; cmp reg, imm
            code = f"pushf;push {reg};mov {reg}, {imm};lea {reg}, [{reg}+0];cmp {reg}, {imm}; pop {reg};popf"
        elif pattern == 12:
            # Pattern 13: mov reg, imm; test reg, reg
            code = f"pushf;push {reg};mov {reg}, {imm};test {reg}, {reg}; pop {reg};popf"
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
                if probability < self.bogus_probability:
                    # an -ebi trampoline keeps a short jrcxz to its local
                    # target: a bogus block inserted inside the span would
                    # push that distance out of rel8 range
                    insertion_point = (instr.new_instruction.address
                                       + instr.new_instruction.size)
                    if self.inside_short_branch_span(insertion_point):
                        continue
                    re_iterate = True
                    inserted_instr = 0

                    # trash_block = bytearray()

                    block_size = random.randint(5,10)

                    # appendi popf come pr
                    # for i in range(block_size):
                    #     trash_block.append(0x90)
                    try:
                        code = self.generate_assembly_tautology()

                        if code == "nop":
                            continue
                        asm, _ = self.ks.asm(code, instr.new_instruction.address + instr.new_instruction.size)
                    except Exception as e:
                        print("Errore in bogus_control_flow(): ",e)
                        print("CODE: ",code)
                        traceback.print_exc()
                        continue
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
                            # The je must land on `instr`, after the NOPs, not
                            # on a hand-computed offset. Registering it lets
                            # update_label_table() repatch it after every later
                            # insertion/morph.
                            self.short_label_table.append((new_instr, instr))
                        tmp_inserted_instr +=  1
                    # faccio break perche' dovro' fare la reiterazione
                    inserted_instr = tmp_inserted_instr
                    break

    # function that will modify instructions to make some different instructions that does the same thing
    def equal_instructions(self):
        change_num = 0
        bytes_added = 0
        for num_instr,instr in enumerate(self.instructions):
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

    def assembly_wrapping(self, seed=None, ghost_probability=0.20,
                          junk_probability=0.15):
        """Assembly wrapping: hide every instruction inside `mov r64, imm64`.

        The final instruction stream (after the other morphing steps and
        after update_label_table()) is rewritten as a chain of 10-byte
        containers: the real bytes live inside the immediate and a
        position-independent entry stub sends the CPU there, so a linear or
        recursive disassembler only sees a run of `mov reg, imm64`.

        The payload must be fully disassembled, and getpc inline data must
        have been moved first (--extract-data), because wrapping changes every
        instruction address.  See asm_wrap.py for the technique itself.
        """
        try:
            from asm_wrap import AssemblyWrapping, WrapItem, WrapError
        except ImportError as error:            # pragma: no cover
            raise RuntimeError(f"-wrap needs asm_wrap.py: {error}")

        if self.sweep_coverage != len(self.raw_code):
            raise RuntimeError(
                f"-wrap needs a fully disassembled payload "
                f"({self.sweep_coverage}/{len(self.raw_code)} bytes covered); "
                "the untouched tail would stay outside the wrapped stream")

        if self.jump_table:
            print("[wrap] WARNING: jump tables present; their code addresses "
                  "are not relocated by this pass")

        # A loop/jcxz branch keeps rel8: if morphing left one with a target
        # that moved, expand it into the near-jump trampoline before wrapping.
        loop_mnemonics = ("loop", "loope", "loopne", "jcxz", "jecxz", "jrcxz")
        if any(instr.new_instruction.mnemonic in loop_mnemonics
               for instr in self.instructions):
            print("[wrap] expanding the remaining loop/jcxz branches")
            self.eliminate_bad_instructions()
            self.update_label_table()
        remaining = [instr.new_instruction.address for instr in self.instructions
                     if instr.new_instruction.mnemonic in loop_mnemonics
                     and not instr.bad_expanded]
        if remaining:
            raise RuntimeError(
                "-wrap cannot relocate the loop/jcxz branches at "
                + ", ".join(hex(address) for address in remaining[:4])
                + "; they have no label entry (see -ebi)")

        if not self.data_analysis_done:
            by_address = {instr.new_instruction.address: instr
                          for instr in self.instructions}

            def is_getpc(instr):
                insn = instr.new_instruction
                if insn.mnemonic != "call" or not insn.operands:
                    return False
                if insn.operands[0].type != x86_const.X86_OP_IMM:
                    return False
                target = by_address.get(insn.operands[0].imm)
                return (target is not None
                        and target.new_instruction.mnemonic == "pop")

            if any(is_getpc(instr) for instr in self.instructions):
                raise RuntimeError(
                    "payload uses a getpc call/pop sequence: run with "
                    "--extract-data before -wrap")

        for instr in self.instructions:
            insn = instr.new_instruction
            if insn.mnemonic == ".byte" or insn.id == 0:
                raise RuntimeError(
                    f"the bytes at {insn.address:#x} are not code (Capstone "
                    "could not decode them): this is inline data, run with "
                    "--extract-data before -wrap")
            if (insn.mnemonic == "call" and len(insn.operands) == 1
                    and insn.operands[0].type == x86_const.X86_OP_IMM
                    and insn.operands[0].imm == insn.address + insn.size
                    and not self.data_analysis_done):
                raise RuntimeError(
                    "payload uses a getpc sequence (call/pop) at "
                    f"{insn.address:#x}: run with --extract-data so the "
                    "inline data is moved before -wrap")

        items = []
        by_key = {}
        for instr in self.instructions:
            insn = instr.new_instruction
            key = id(instr)
            by_key[key] = instr
            items.append(WrapItem(
                key=key,
                addr=insn.address,
                data=bytes(insn.bytes),
                forced_raw=bool(instr.bad_expanded),
                data_fixup=instr.data_ref_fixup is not None))

        wrapper = AssemblyWrapping(seed=seed,
                                   ghost_probability=ghost_probability,
                                   junk_probability=junk_probability)
        try:
            wrapper.plan(items)
        except WrapError as error:
            raise RuntimeError(f"assembly wrapping failed: {error}") from error

        # short branches may have been promoted to their near forms
        for item in items:
            instr = by_key[item.key]
            decoded = next(self.cs.disasm(
                item.data, instr.new_instruction.address, count=1), None)
            if decoded is None or decoded.size != len(item.data):
                raise RuntimeError(
                    "cannot re-decode the normalised instruction at "
                    f"{item.addr:#x}")
            instr.new_instruction = decoded

        self.layout_override = {item.key: wrapper.new_address[item.key]
                                for item in items}
        self.code_length_override = wrapper.code_length

        # the displacement of a `lea r64, [rip + d]` depends on the final
        # wrapped address, so the data layer must run after the layout
        if self.extracted_data:
            self.finalize_data_refs()

        try:
            payload = wrapper.render(
                lambda key: bytes(by_key[key].new_instruction.bytes))
        except WrapError as error:
            raise RuntimeError(f"assembly wrapping failed: {error}") from error

        self.final_payload_bytes = payload
        self.morph_applied = True
        print(wrapper.describe())
        return payload

    def write_strange_file(self, out_file = None):
        if self.extracted_data and not self.data_refs_finalized:
            # Finalize before serialising the instruction bytes: a late
            # finalize would update new_instruction after new_bytes was
            # already assembled.
            self.finalize_data_refs()
        new_bytes = b''
        for x,i in enumerate(self.instructions):
            new_bytes += i.new_instruction.bytes

        padding1 = self.mem_address - len(new_bytes)
        # add 
        new_bytes += bytearray([0x90 for _ in range(padding1)])

        # create a bytearray of the instruction map
        map_bytes = b''
        for x,i in enumerate(self.instr_mapping):
            map_bytes += int(i[1]).to_bytes(8, byteorder='little', signed=True)

        new_bytes += map_bytes

        # extracted data lives after the PII instruction map
        if self.extracted_data:
            new_bytes += self.final_data_pad
            new_bytes += self.final_data_blob
        
        if out_file == None:
            out_file = 'new_payload.bin'
        # non modificare il file esistente, creano uno nuovo
        with open(out_file, 'wb') as f:
            f.seek(0)
            f.write(new_bytes)
    
    def write_file(self, out_file = None):
        if self.final_payload_bytes is not None:
            # an assembly-wrapping pass produced the whole code area
            new_bytes = self.final_payload_bytes
            if self.extracted_data:
                if not self.data_refs_finalized:
                    self.finalize_data_refs()
                new_bytes += self.final_data_pad
                new_bytes += self.final_data_blob
            if out_file == None:
                out_file = 'new_payload.bin'
            with open(out_file, 'wb') as f:
                f.seek(0)
                f.write(new_bytes)
            return

        if self.extracted_data and not self.data_refs_finalized:
            # Must run before the instruction bytes are concatenated.
            self.finalize_data_refs()

        new_bytes = b''
        for i in self.instructions:
            new_bytes += i.new_instruction.bytes

        # data extracted with --extract-data goes after the code
        if self.extracted_data:
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
        if out_file == None:
            out_file = 'new_payload.bin'
        with open(out_file, 'wb') as f:
            f.seek(0)
            f.write(new_bytes)


def eliminate_instr(type, file):
    if file == None:
        if len(sys.argv) < 2:
            print_usage()
            exit(1)
        zone = Zone(sys.argv[1])
    else:
        zone = Zone(file)
    zone.create_jmp_table()
    zone.create_label_table()

    if type == 'loop':
        zone.eliminate_loop_instructions()
        
    elif type == 'jrcxz':
        zone.eliminate_jrcxz_instructions()
    
    zone.update_label_table()
    zone.write_file()

def _wrap_seed():
    """ZONE_WRAP_SEED makes the random wrapping reproducible."""
    raw = os.environ.get("ZONE_WRAP_SEED", "")
    if not raw:
        return None
    try:
        return int(raw, 0)
    except ValueError:
        return None


def _wrap_fraction(name, default):
    """Read a probability override from the environment."""
    raw = os.environ.get(name, "")
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return min(max(value, 0.0), 1.0)


def print_usage():
    print("Usage: python pobf.py <file> <options>")
    print("Options:")
    print("--help                                           Show  this help message and exit")
    print("--equal-instructions, -eq                        Modify instructions to make them equal")
    print("--bogus-cf, -bcf                                 Add bogus control flow instructions")
    print("--insert-nop, -nop                               Insert NOP instructions")
    print("--instruction-block-permutation, -ibp            Permute instruction blocks")
    print("--position-independent-instr, -pii               Indexed PII dispatcher (works with -xd)")
    print("--instruction-permutation, -ip                   Permute single instructions (works with -xd)")
    print("--assembly-wrapping, -wrap                       Hide instructions inside mov reg64, imm64 (x64, implies -ebi)")
    print("--find-data, -fd                                 Find data with symbolic exploration and exit")
    print("--extract-data, -xd                              Move data to the end of the payload and fix references")
    print("--extract-unknown, -xu                           Also move outside_cfg ranges (risky)")
    print("--eliminate-bad-instructions, -ebi               Expand jrcxz/loop short branches before morphing")
    print("--data-timeout <seconds>                         Symbolic exploration timeout (default 120)")
    print("--data-cache <file>                              Data cache (default data_cache.json)")
    print("--no-data-cache, -nc                             Disable the data cache")
    print("--refresh-data-cache, -rc                        Ignore and replace the cached entry")
    print("--output,-o <file>                               Output file name")
    print("--llm                                            Let DeepSeek apply the selected technique")
    print("--llm-technique <eq|nop|bcf|ibp>                 Technique the LLM must apply")
    print("--llm-shots <n>                                  Worked examples in the prompt (default 1)")
    print("--llm-data, --llm-classify-data                  LLM data classification instead of -xd")
    print("--llm-data-json <file>                           Save the data classification JSON")
    print("--llm-model <id>                                 Model id (default deepseek-flash)")
    print("--llm-base-url <url>                             API base URL (default api.deepseek.com/v1)")
    print("--llm-timeout <seconds>                          HTTP timeout (default 180)")
    print("--llm-retries <n>                                Generation attempts (default 3)")
    print("--llm-max-tokens <n>                             Maximum response tokens (default 32768)")
    print("--llm-temperature <float>                        Sampling temperature (default 0.2)")
    print("--llm-verify <static|messagebox>                 Verification after assembly (default static)")
    print("--llm-no-extract-data                            Do not run -xd automatically before the LLM")
    print("--llm-min-similarity <float>                     Override the structural similarity floor")
    print("--llm-dump-prompt <file>                         Save the full prompt")
    print("--llm-dump-response <file>                       Save the last raw response")
    print("--llm-mock-response <file>                       Use a local response instead of the API")
    print("--llm-failed-output <file>                       Save the last rejected answer")
    print("--llm-stats <file>                               Save token/time/cost statistics as JSON")



def start(file):

    equal_instr = False
    bogus_cf = False
    insert_nop = False
    instruction_block_permutation = False
    position_independent_instr = False
    instruction_permutation = False
    assembly_wrapping = False
    find_data = False
    extract_data = False
    extract_unknown = False
    eliminate_bad = False
    data_timeout = 120.0
    data_cache = "data_cache.json"
    no_data_cache = False
    refresh_data_cache = False
    llm_mode = False
    llm_morph = False
    llm_technique = None
    llm_model = None
    llm_base_url = None
    llm_timeout = None
    llm_retries = None
    llm_max_tokens = None
    llm_temperature = None
    llm_verify = "static"
    llm_no_extract_data = False
    llm_min_similarity = None
    llm_dump_prompt = None
    llm_dump_response = None
    llm_mock_response = None
    llm_failed_output = "llm_failed.asm"
    llm_stats_path = None
    llm_shots = 1
    llm_data = False
    llm_data_json = None

    if file == None:
        if len(sys.argv) < 2:
            print_usage()
            exit(1)
        if sys.argv[1] == "--help" or "--help" in sys.argv[2:]:
            print_usage()
            sys.exit(0)
        zone = Zone(sys.argv[1])
    else:
        zone = Zone(file)
    
    brain_activate = True
    
    opt_args = sys.argv[1:]
    output_file = None
    for arg in opt_args:
        if arg == "--help":
            print_usage()
            sys.exit(0)
        elif arg == "--equal-instructions" or arg == "-eq":
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
        elif arg == "--assembly-wrapping" or arg == "-wrap":
            assembly_wrapping = True
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
        elif arg == "--llm" or arg == "-llm":
            llm_mode = True
            llm_morph = True
        elif arg == "--llm-technique":
            try:
                llm_technique = opt_args[opt_args.index(arg) + 1]
            except IndexError:
                print("--llm-technique requires a name")
                sys.exit(1)
            llm_mode = True
            llm_morph = True
        elif arg == "--llm-shots":
            try:
                llm_shots = int(opt_args[opt_args.index(arg) + 1])
            except (IndexError, ValueError):
                print("--llm-shots requires an integer")
                sys.exit(1)
        elif (arg == "--llm-data" or arg == "--llm-classify-data"
              or arg == "--llm-xd"):
            llm_data = True
            llm_mode = True
        elif arg == "--llm-data-json":
            try:
                llm_data_json = opt_args[opt_args.index(arg) + 1]
            except IndexError:
                print("--llm-data-json requires a file name")
                sys.exit(1)
        elif arg == "--llm-model":
            try:
                llm_model = opt_args[opt_args.index(arg) + 1]
            except IndexError:
                print("--llm-model requires a model id")
                sys.exit(1)
        elif arg == "--llm-base-url":
            try:
                llm_base_url = opt_args[opt_args.index(arg) + 1]
            except IndexError:
                print("--llm-base-url requires a URL")
                sys.exit(1)
        elif arg == "--llm-timeout":
            try:
                llm_timeout = float(opt_args[opt_args.index(arg) + 1])
            except (IndexError, ValueError):
                print("--llm-timeout requires a number of seconds")
                sys.exit(1)
        elif arg == "--llm-retries":
            try:
                llm_retries = int(opt_args[opt_args.index(arg) + 1])
            except (IndexError, ValueError):
                print("--llm-retries requires an integer")
                sys.exit(1)
        elif arg == "--llm-max-tokens":
            try:
                llm_max_tokens = int(opt_args[opt_args.index(arg) + 1])
            except (IndexError, ValueError):
                print("--llm-max-tokens requires an integer")
                sys.exit(1)
        elif arg == "--llm-temperature":
            try:
                llm_temperature = float(opt_args[opt_args.index(arg) + 1])
            except (IndexError, ValueError):
                print("--llm-temperature requires a number")
                sys.exit(1)
        elif arg == "--llm-verify":
            try:
                llm_verify = opt_args[opt_args.index(arg) + 1]
            except IndexError:
                print("--llm-verify requires static or messagebox")
                sys.exit(1)
        elif arg == "--llm-no-extract-data":
            llm_no_extract_data = True
        elif arg == "--llm-min-similarity":
            try:
                llm_min_similarity = float(opt_args[opt_args.index(arg) + 1])
            except (IndexError, ValueError):
                print("--llm-min-similarity requires a number")
                sys.exit(1)
        elif arg == "--llm-dump-prompt":
            try:
                llm_dump_prompt = opt_args[opt_args.index(arg) + 1]
            except IndexError:
                print("--llm-dump-prompt requires a file name")
                sys.exit(1)
        elif arg == "--llm-dump-response":
            try:
                llm_dump_response = opt_args[opt_args.index(arg) + 1]
            except IndexError:
                print("--llm-dump-response requires a file name")
                sys.exit(1)
        elif arg == "--llm-mock-response":
            try:
                llm_mock_response = opt_args[opt_args.index(arg) + 1]
            except IndexError:
                print("--llm-mock-response requires a file name")
                sys.exit(1)
        elif arg == "--llm-failed-output":
            try:
                llm_failed_output = opt_args[opt_args.index(arg) + 1]
            except IndexError:
                print("--llm-failed-output requires a file name")
                sys.exit(1)
        elif arg == "--llm-stats":
            try:
                llm_stats_path = opt_args[opt_args.index(arg) + 1]
            except IndexError:
                print("--llm-stats requires a file name")
                sys.exit(1)
    print("OPT_ARGS: ", opt_args)

    if data_timeout < 0:
        print("--data-timeout must be nonnegative")
        sys.exit(1)

    if position_independent_instr and instruction_permutation:
        print("ERROR: -pii and -ip are different techniques; choose one")
        sys.exit(1)

    if extract_data and position_independent_instr:
        print("[pii] indexed dispatcher; data blob goes after the "
              "instruction map")

    if instruction_permutation and not eliminate_bad:
        print("[ip] enabling short-branch expansion for instruction permutation")
        eliminate_bad = True

    if position_independent_instr and not eliminate_bad:
        print("[pii] enabling short-branch expansion for PII dispatcher")
        eliminate_bad = True

    if assembly_wrapping and (position_independent_instr
                              or instruction_permutation):
        print("ERROR: -wrap cannot be combined with -pii or -ip: both "
              "techniques rewrite the whole layout")
        sys.exit(1)

    if assembly_wrapping and not eliminate_bad:
        # a loop/jrcxz that was a few bytes away would leave rel8 range once
        # its code is moved inside a container
        print("[wrap] enabling short-branch expansion for assembly wrapping")
        eliminate_bad = True

    morph_requested = (equal_instr or instruction_block_permutation
                       or bogus_cf or insert_nop)
    if (morph_requested or eliminate_bad or position_independent_instr
            or instruction_permutation or assembly_wrapping):
        zone.morph_applied = True

# LLM MODE: the model applies the selected technique as a full assembly rewrite

    if llm_mode:
        import llm_technique as llm_engine
        import llm_payload
        import llm_data as llm_data_engine

        if find_data:
            print("ERROR: --llm cannot be combined with --find-data")
            sys.exit(1)
        if llm_data and (find_data or extract_data):
            print("ERROR: --llm-data is an alternative to -xd/-fd; choose one")
            sys.exit(1)
        if llm_data and llm_no_extract_data:
            print("ERROR: --llm-data cannot be combined with "
                  "--llm-no-extract-data")
            sys.exit(1)
        if eliminate_bad:
            print("[llm] note: -ebi is not applied in LLM mode; the model is "
                  "instructed to expand loop/jcxz when a target exceeds rel8")

        selected = []
        if equal_instr:
            selected.append("eq")
        if insert_nop:
            selected.append("nop")
        if bogus_cf:
            selected.append("bcf")
        if instruction_block_permutation:
            selected.append("ibp")
        if position_independent_instr:
            selected.append("pii")
        if instruction_permutation:
            selected.append("ip")
        if assembly_wrapping:
            selected.append("wrap")

        technique = None
        try:
            if llm_morph:
                if llm_technique:
                    technique = llm_engine.resolve_technique(llm_technique)
                    if selected and technique not in selected:
                        raise llm_engine.LLMConfigError(
                            f"--llm-technique {technique} does not match the "
                            f"selected flag(s): {', '.join(selected)}")
                    if len(selected) > 1:
                        raise llm_engine.LLMConfigError(
                            "LLM mode applies one technique at a time; pass "
                            "only one of -eq, -nop, -bcf, -ibp")
                elif selected:
                    if len(selected) > 1:
                        raise llm_engine.LLMConfigError(
                            "LLM mode applies one technique at a time; pass "
                            "only one of -eq, -nop, -bcf, -ibp")
                    technique = selected[0]
                elif not llm_data:
                    raise llm_engine.LLMConfigError(
                        "LLM mode needs a technique or --llm-data: pass one "
                        "of -eq, -nop, -bcf, -ibp, or --llm-data")
                if technique is not None and technique not in llm_engine.TECHNIQUES:
                    raise llm_engine.LLMConfigError(
                        f"LLM mode does not implement {technique!r} yet; "
                        "supported: eq, nop, bcf, ibp (use the native "
                        "-pii/-ip/-wrap implementation for the others)")
            else:
                # --llm-data without --llm: the selected technique flags are
                # native Zone transformations, applied after LLM data
                # classification.  All native techniques are allowed here.
                if llm_technique:
                    raise llm_engine.LLMConfigError(
                        "--llm-technique selects LLM morphing; use --llm with "
                        "it, or use native technique flags with --llm-data")
        except llm_engine.LLMConfigError as error:
            print(f"ERROR: {error}")
            sys.exit(1)

        native_after = bool(llm_data and not llm_morph and selected)

        if llm_verify not in ("static", "messagebox"):
            print("ERROR: --llm-verify must be static or messagebox")
            sys.exit(1)

        api_key = None
        if not llm_mock_response:
            try:
                api_key = llm_engine.resolve_api_key()
            except llm_engine.LLMConfigError as error:
                print(f"ERROR: {error}")
                sys.exit(1)

        options = llm_engine.LLMOptions(
            technique=(technique or "data"),
            arch="x64",
            model=(llm_model or os.environ.get("ZONE_LLM_MODEL")
                   or llm_engine.DEFAULT_MODEL),
            base_url=(llm_base_url or os.environ.get("ZONE_LLM_BASE_URL")
                      or os.environ.get("DEEPSEEK_BASE_URL")
                      or llm_engine.DEFAULT_BASE_URL),
            api_key=api_key,
            temperature=(llm_temperature if llm_temperature is not None
                         else 0.2),
            max_tokens=(llm_max_tokens if llm_max_tokens is not None
                        else llm_engine.DEFAULT_MAX_TOKENS),
            timeout=(llm_timeout if llm_timeout is not None
                     else llm_engine.DEFAULT_TIMEOUT),
            retries=(llm_retries if llm_retries is not None else 3),
            verify=llm_verify,
            dump_prompt=llm_dump_prompt,
            dump_response=llm_dump_response,
            mock_response=llm_mock_response,
            min_similarity=llm_min_similarity,
            stats_path=llm_stats_path,
            shots=llm_shots,
        )

        print(f"[llm] technique={technique or 'data-classification'} "
              f"model={options.model}")
        print(f"[llm] endpoint={llm_engine._endpoint(options.base_url)}")

        data_result = None
        if llm_data:
            print("[llm] classifying data with the model instead of -xd")
            try:
                data_result = llm_data_engine.run_data(
                    lambda: zone.__class__(zone.file),
                    zone.raw_code, "x64", options,
                    dump_prompt=llm_dump_prompt,
                    dump_response=llm_dump_response)
            except llm_engine.LLMGenerationError as error:
                if error.last_source and llm_failed_output:
                    with open(llm_failed_output, "w", encoding="utf-8",
                              newline="\n") as handle:
                        handle.write(error.last_source)
                    print(f"[llm] last rejected answer saved to "
                          f"{llm_failed_output}")
                if error.stats is not None:
                    print(error.stats.summary())
                    if llm_stats_path:
                        path = (llm_stats_path if technique is None
                                else llm_stats_path + ".data.json")
                        error.stats.write_json(path)
                        print(f"[llm] data stats JSON: {path}")
                print(f"ERROR: {error}")
                sys.exit(1)
            except llm_engine.LLMError as error:
                stats = getattr(error, "stats", None)
                if stats is not None:
                    print(stats.summary())
                    if llm_stats_path:
                        path = (llm_stats_path if technique is None
                                else llm_stats_path + ".data.json")
                        stats.write_json(path)
                        print(f"[llm] data stats JSON: {path}")
                print(f"ERROR: {error}")
                sys.exit(1)

            zone = data_result.zone
            print(data_result.stats.summary())
            if llm_stats_path:
                path = (llm_stats_path if technique is None
                        else llm_stats_path + ".data.json")
                data_result.stats.write_json(path)
                print(f"[llm] data stats JSON: {path}")
            if llm_data_json:
                data_result.write_json(llm_data_json)
                print(f"[llm] data classification JSON: {llm_data_json}")
            print(f"[llm] data classification: "
                  f"{len(data_result.sections)} section(s), "
                  f"{data_result.data_bytes} bytes")
            if native_after:
                # Native Zone techniques will run after this block.  Let
                # write_file() finalize the data references again at the
                # final layout instead of keeping the pre-morph addresses.
                zone.data_refs_finalized = False
            if technique is None and not native_after:
                out = output_file if output_file else "new_payload.bin"
                zone.write_file(out)
                with open(out, "rb") as handle:
                    output_bytes = handle.read()
                print(f"[llm] wrote {out} ({len(output_bytes)} bytes, "
                      "data-only mode)")
                print(f"Output: {out}")
                if llm_verify == "messagebox":
                    ok, detail = llm_engine.verify_messagebox_bytes(
                        output_bytes, "x64")
                    print(f"[llm] execution check: {detail}")
                    if not ok:
                        print("ERROR: data-only output failed the message-box "
                              "check")
                        sys.exit(1)
                return
        else:
            do_extract = extract_data or not llm_no_extract_data
            if do_extract:
                print("[llm] extracting data before canonicalisation "
                      "(use --llm-no-extract-data to skip)")
                sections, xrefs = zone.analyze_data(
                    timeout=data_timeout,
                    print_strings=False,
                    cache_path=data_cache,
                    use_cache=not no_data_cache,
                    refresh_cache=refresh_data_cache,
                )
                zone.extract_data(sections, xrefs,
                                  include_unknown=extract_unknown)
                zone.data_analysis_done = True
                zone.finalize_data_refs()
            else:
                print("[llm] data extraction skipped")
                # The selected technique flag set morph_applied, but no native
                # morph happened: keep an untouched sweep tail if the payload
                # has one.
                zone.morph_applied = False
                if zone.sweep_coverage != len(zone.raw_code):
                    print("[llm] WARNING: the payload has undecodable bytes; "
                          "without -xd the canonical listing may contain data")

        if llm_morph:
            # No native morph ran before this point: do not suppress a sweep
            # tail when the data layer found nothing.
            zone.morph_applied = False
            try:
                canonical = llm_payload.from_zone(zone, "x64")
            except llm_payload.LLMPayloadError as error:
                print(f"ERROR: cannot canonicalise the payload: {error}")
                sys.exit(1)
            print(f"[llm] canonical listing: {len(canonical.code)} code "
                  f"bytes, {len(canonical.blob)} data bytes, "
                  f"{len(canonical.ret_labels)} getpc site(s)")

            verifier = None
            if llm_verify == "messagebox":
                verifier = lambda data: llm_engine.verify_messagebox_bytes(
                    data, "x64")

            try:
                result = llm_engine.run(canonical, options,
                                        verifier=verifier)
            except llm_engine.LLMGenerationError as error:
                if error.last_source and llm_failed_output:
                    with open(llm_failed_output, "w", encoding="utf-8",
                              newline="\n") as handle:
                        handle.write(error.last_source)
                    print(f"[llm] last rejected answer saved to "
                          f"{llm_failed_output}")
                if error.stats is not None:
                    print(error.stats.summary())
                    if llm_stats_path:
                        error.stats.write_json(llm_stats_path)
                        print(f"[llm] stats JSON: {llm_stats_path}")
                print(f"ERROR: {error}")
                sys.exit(1)
            except llm_engine.LLMError as error:
                stats = getattr(error, "stats", None)
                if stats is not None:
                    print(stats.summary())
                    if llm_stats_path:
                        stats.write_json(llm_stats_path)
                        print(f"[llm] stats JSON: {llm_stats_path}")
                print(f"ERROR: {error}")
                sys.exit(1)

            out = output_file if output_file else "new_payload.bin"
            with open(out, "wb") as handle:
                handle.write(result.payload)
            print(f"[llm] wrote {out} ({len(result.payload)} bytes, "
                  f"{result.attempts} attempt(s))")
            print(f"Output: {out}")
            if result.stats is not None:
                print(result.stats.summary())
                if llm_stats_path:
                    result.stats.write_json(llm_stats_path)
                    print(f"[llm] stats JSON: {llm_stats_path}")
            return

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
            exit(0)

        zone.extract_data(sections, xrefs, include_unknown=extract_unknown)
        zone.data_analysis_done = True


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

        if assembly_wrapping:
            zone.assembly_wrapping(
                seed=_wrap_seed(),
                ghost_probability=_wrap_fraction("ZONE_WRAP_GHOST", 0.20),
                junk_probability=_wrap_fraction("ZONE_WRAP_JUNK", 0.15))

        # the final layout is known only now: fill in the data displacements
        zone.finalize_data_refs()
        zone.print_instructions()
        if position_independent_instr:
            zone.write_strange_file(output_file)
        else:
            zone.write_file(output_file)
        zone.print_instructions()
        print(f"Output: {output_file if output_file else 'new_payload.bin'}")
        print("FINE")
        exit(0)

# NORMAL PIPELINE

    if (morph_requested or eliminate_bad or position_independent_instr
            or instruction_permutation):
        try:
            zone.create_jmp_table()
        except Exception as e:
            print("create_jmp_table() skipped: ", e)
        zone.create_label_table()

    if eliminate_bad:
        zone.eliminate_bad_instructions()
    
    # zone.update_label_table()
    

# CODE MODIFICATION
    if equal_instr == True:
        zone.equal_instructions()
    # zone.insert_random_
    # 
    # 
    # nop()
    if instruction_block_permutation == True:
        zone.chaos_cf()
        zone.shuffle_blocks()

    if bogus_cf == True:
        zone.bogus_control_flow()
    if insert_nop == True:
        zone.insert_random_nop()
    # zone.update_label_table()
    if position_independent_instr == True:
        zone.pii_dispatcher_v2()
    elif instruction_permutation == True:
        zone.pii_permute_instructions()
    # while check == False:
    # check = zone.check_jcrxz_ok()



# CODE PATCHING
    if (not position_independent_instr
            and (morph_requested or eliminate_bad or instruction_permutation)):
        zone.update_label_table()
    zone.print_blocks()

    if assembly_wrapping:
        zone.assembly_wrapping(
            seed=_wrap_seed(),
            ghost_probability=_wrap_fraction("ZONE_WRAP_GHOST", 0.20),
            junk_probability=_wrap_fraction("ZONE_WRAP_JUNK", 0.15))

    zone.print_instructions()
    # zone.adjust_out_text_references()

    # zone.adjust_reloc_table()
    # zone.adjust_jmp_table()

# WRITE MODIFICATION
    if position_independent_instr == True:
        zone.write_strange_file(output_file)
    else:
        zone.write_file(output_file)
    zone.print_instructions()
    if llm_data and llm_verify == "messagebox":
        out = output_file if output_file else "new_payload.bin"
        with open(out, "rb") as handle:
            output_bytes = handle.read()
        ok, detail = llm_engine.verify_messagebox_bytes(output_bytes, "x64")
        print(f"[llm] execution check: {detail}")
        if not ok:
            print("ERROR: native morph output failed the message-box check")
            sys.exit(1)
    print("FINE")
    

if __name__ == "__main__":
    start(None)
