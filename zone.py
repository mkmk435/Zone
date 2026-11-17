#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Zone - PE bin2bin rewriter (v2).

Questa e' la versione PE di Zone riscritta.  A differenza della v1 (che
disassemblava la .text in modo lineare, patchava le reference con delle
regex sull'op_str e allargava la sezione di una quantita' fissa) qui il
layout viene ricalcolato da zero e *tutte* le reference sono tracciate,
sulla falsariga di come funziona binprotect (noahware):

  * code discovery: recursive descent da seed strutturali (entry point,
    export, .pdata RUNTIME_FUNCTION, TLS callbacks, reloc che puntano
    nel codice) con splitting dei basic block; quello che non e'
    raggiungibile resta DATA e non viene toccato;
  * un solo modello di indirizzi: ogni item (istruzione o blocco dati)
    ha una vecchia RVA e una nuova RVA; esiste una sola funzione
    map_point() usata da qualunque patch;
  * reference: branch rel8/rel32, operandi RIP-relative, disp32
    assoluti, imm64, jump table (MSVC / LLVM / GCC), reloc, .pdata e
    unwind info, scope table SEH, import/export/resource/debug/TLS/
    load config/delay import, piu' una scansione opzionale dei puntatori
    nei dati;
  * crescita della sezione calcolata sul bisogno reale (non piu'
    0x18000 fissi) e allineata a SectionAlignment, quindi nessun troncamento
    silenzioso del codice;
  * le funzioni con exception handler (C++ EH / SEH) e i prologhi
    descritti dall'unwind info non vengono MAI modificati, perche'
    gli offset in quelle strutture sono relativi all'inizio funzione.

Compatibilita': i nomi dei metodi della v1 (create_label_table,
equal_instructions, insert_random_nop, update_label_table,
adjust_out_text_references, adjust_reloc_table, adjust_jmp_table,
write_pe_file) sono mantenuti, cosi' gli script esistenti continuano a
funzionare.

Uso:
    python zone.py payload.exe                 # scrive payload_zone.exe
    python zone.py payload.exe -o out.exe      # nome esplicito
    python zone.py payload.exe --eq --nop --bcf --ibp --ebi
    python zone.py payload.exe --check         # verifica le reference
    python zone.py payload.exe --in-place      # sovrascrive l'input
"""

from __future__ import annotations

import argparse
import bisect
import os
import random
import struct
import sys

import pefile
from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86 import (
    X86_GRP_BRANCH_RELATIVE,
    X86_GRP_CALL,
    X86_GRP_INT,
    X86_GRP_IRET,
    X86_GRP_JUMP,
    X86_GRP_RET,
    X86_INS_CALL,
    X86_INS_HLT,
    X86_INS_INT3,
    X86_INS_IRET,
    X86_INS_JMP,
    X86_INS_RET,
    X86_INS_UD2,
    X86_OP_IMM,
    X86_OP_MEM,
    X86_OP_REG,
    X86_REG_RIP,
    X86_REG_RIZ,
)
from keystone import KS_ARCH_X86, KS_MODE_64, Ks


class ZoneError(Exception):
    """Errore bloccante: meglio fermarsi che produrre un binario rotto."""


# ---------------------------------------------------------------------------
# utilita'
# ---------------------------------------------------------------------------

def align_up(value, alignment):
    if alignment <= 1:
        return value
    return (value + alignment - 1) // alignment * alignment


def p32(value):
    if not -(2 ** 31) <= value < 2 ** 31:
        raise ZoneError("disp32 fuori range: %d" % value)
    return struct.pack("<i", value)


def p64(value):
    return struct.pack("<Q", value & 0xFFFFFFFFFFFFFFFF)


def is_moved_section(section):
    """Le sezioni con dati eseguibili/leggibili che si spostano."""
    return bool(section.Characteristics & 0x80000000)  # IMAGE_SCN_MEM_WRITE? no


class _EncodedInsn:
    """Piccolo shim con la stessa interfaccia degli oggetti capstone.

    Serve a mantenere compatibile l'API della v1: gli script che leggono
    instr.new_instruction.bytes / .address / .mnemonic continuano a
    funzionare.
    """

    __slots__ = ("address", "bytes", "size", "mnemonic", "op_str", "id", "groups")

    def __init__(self, address, raw, mnemonic, op_str, insn_id=None, groups=()):
        self.address = address
        self.bytes = bytes(raw)
        self.size = len(raw)
        self.mnemonic = mnemonic
        self.op_str = op_str
        self.id = insn_id
        self.groups = list(groups)


# ---------------------------------------------------------------------------
# item del layout
# ---------------------------------------------------------------------------

class Instruction:
    """Un item del layout: istruzione, blocco dati o sequenza inserita."""

    __slots__ = (
        "kind", "old_rva", "orig_size", "size", "orig_bytes", "data",
        "replacement", "cs_insn", "target_old", "is_branch", "is_cond",
        "is_uncond", "imm_off", "imm_size", "disp_off", "disp_size",
        "rip_target", "abs_target", "abs_size", "abs_va", "abs_is_mem", "new_rva",
        "new_bytes", "opcode", "no_resize", "label", "role", "target_item",
        "old_instruction",
        "new_instruction", "original_instruction", "prev_instruction",
        "next_instruction", "address_history", "bad_expanded", "data_ref_fixup",
    )

    def __init__(self, kind, old_rva, size, data=b""):
        self.kind = kind                # 'insn' | 'data' | 'seq'
        self.old_rva = old_rva
        self.orig_size = size
        self.size = size
        self.orig_bytes = data
        self.data = data
        self.replacement = None
        self.cs_insn = None
        self.target_old = None
        self.is_branch = False
        self.is_cond = False
        self.is_uncond = False
        self.imm_off = 0
        self.imm_size = 0
        self.disp_off = 0
        self.disp_size = 0
        self.rip_target = None
        self.abs_target = None
        self.abs_size = 0
        self.abs_va = False
        self.abs_is_mem = False
        self.new_rva = 0
        self.new_bytes = b""
        self.opcode = None
        self.no_resize = False
        self.label = None
        # 'nop' (sacrificabile), 'connector'/'bcf'/'tramp' (strutturali:
        # non vanno mai rimossi per far stare il layout)
        self.role = None
        # per i branch creati da noi: target come item (funziona anche se
        # il blocco di destinazione non ha una RVA vecchia, es. trampolini)
        self.target_item = None
        # compatibilita' con la v1
        self.old_instruction = None
        self.new_instruction = None
        self.original_instruction = None
        self.prev_instruction = None
        self.next_instruction = None
        self.address_history = []
        self.bad_expanded = False
        self.data_ref_fixup = None

    # -- usato dal layout
    def reset_size(self):
        if self.kind == "insn":
            self.size = max(self.orig_size, len(self.replacement or b""))

    def __repr__(self):
        if self.kind == "data":
            return "<data %#x size %d>" % (self.old_rva, self.size)
        if self.kind == "seq":
            return "<seq size %d>" % self.size
        return "<insn %#x %s %d>" % (self.old_rva, self.cs_insn.mnemonic, self.size)


# ---------------------------------------------------------------------------
# Zone
# ---------------------------------------------------------------------------

class Zone:

    TERMINATORS = (X86_INS_RET, X86_INS_INT3, X86_INS_UD2, X86_INS_HLT)
    MAX_JMPTABLE = 4096

    def __init__(self, file, seed=None, verbose=True, log=None, growth="slack"):
        self.file = file
        self.verbose = verbose
        self.log_file = log
        self.rng = random.Random(seed)
        if growth not in ("slack", "shift"):
            raise ZoneError("growth deve essere 'slack' o 'shift'")
        self.growth_mode = growth

        self.cs = Cs(CS_ARCH_X86, CS_MODE_64)
        self.cs.detail = True
        self.cs.skipdata = False          # discovery esplicito, niente skipdata
        self.ks = Ks(KS_ARCH_X86, KS_MODE_64)

        self.pe = pefile.PE(file)
        self.data = bytearray(open(file, "rb").read())
        self.image_base = self.pe.OPTIONAL_HEADER.ImageBase

        self.sections = list(self.pe.sections)
        for section in self.sections:
            section._zone_va = section.VirtualAddress
            section._zone_vs = section.Misc_VirtualSize
            section._zone_raw = section.SizeOfRawData
            section._zone_pr = section.PointerToRawData

        # la sezione di codice che riscriviamo
        self.text = self._find_text_section()
        self.text_va = self.text._zone_va
        self.text_vsize = self.text._zone_vs
        self.text_raw_size = self.text._zone_raw
        self.text_raw_off = self.text._zone_pr
        self.text_end_old = self.text_va + self.text_raw_size
        self.text_rva_end_vsize = self.text_va + self.text_vsize

        self.section_alignment = self.pe.OPTIONAL_HEADER.SectionAlignment
        self.file_alignment = self.pe.OPTIONAL_HEADER.FileAlignment

        self.delta = 0
        self.items = []                    # ordine = indirizzo crescente
        self.item_starts = []
        self.insns = {}                    # old_rva -> capstone insn
        self.code_rvas = set()
        self.visits = set()
        self.queue = []
        self.branch_refs = []
        self.rip_refs = []
        self.imm_refs = []
        self.abs_refs = []
        self.jump_tables = []              # (base_old, count, entry_size, mode)
        self.jumptable_ranges = []
        self.data_patch_sites = set()

        # strutture PE
        self.patches = []                  # (site_old_rva, width, mode, target) per report
        self.runtime_functions = []
        self.eh_functions = []             # funzioni con handler: intoccabili
        self.eh_structures = []            # (rva, tipo)
        self.cpp_eh_found = 0

        self.no_resize_ranges = []         # (start,end) dove non si tocca nulla
        self.no_insert_ranges = []         # (start,end) dove non si inserisce
        self.permuted = False              # albero dei blocchi modificato (-ibp)
        self.risky_blocks = []             # blocchi trovati via risky reference

        self.sizes_report = {}

        self._parse_sections()
        self._parse_exception_directory()
        self._collect_seeds()
        self._disassemble()
        # le tabelle di puntatori a codice dentro la .text vanno trovate
        # *prima* del gap probe: i loro target sono codice e i loro byte
        # non sono istruzioni.  Iteriamo finche' non si stabilizza.
        for _ in range(12):
            self._probe_code_gaps()
            found = self._probe_gap_starts()
            found += self._scan_risky_references()
            found += self._scan_code_pointer_tables()
            found += self._scan_data_code_tables()
            if not found:
                break
            self._drain_queue()
        self._purge_code_in_tables()
        self._find_jump_tables()
        self._build_items()
        self._parse_data_refs()

        self.info("sezioni:")
        for s in self.sections:
            self.info("  %-8s VA=%#010x VSize=%#08x Raw=%#08x @%#08x" % (
                s.Name.rstrip(b"\x00").decode(errors="replace"),
                s._zone_va, s._zone_vs, s._zone_raw, s._zone_pr))
        self.info("immagine: %d istruzioni, %d blocchi dati, %d jump table, "
                  "%d runtime function (%d con handler)"
                  % (len(self.insns), sum(1 for i in self.items if i.kind == "data"),
                     len(self.jump_tables), len(self.runtime_functions),
                     len(self.eh_functions)))

    # -- logging ----------------------------------------------------------
    def info(self, message):
        if self.verbose:
            print(message)
            if self.log_file:
                self.log_file.write(str(message) + "\n")

    # -- accesso all'immagine --------------------------------------------
    def _find_text_section(self):
        for section in self.sections:
            if section.Characteristics & 0x20000000:  # IMAGE_SCN_MEM_EXECUTE
                if section._zone_raw:
                    return section
        raise ZoneError("nessuna sezione eseguibile trovata")

    def _parse_sections(self):
        self.moved_sections = [s for s in self.sections
                              if s._zone_va > self.text_va and s._zone_vs]
        for section in self.sections:
            if (section.Characteristics & 0x20000000) and section is not self.text:
                self.info("attenzione: sezione eseguibile secondaria %s (non gestita)"
                          % section.Name)
        # spazio virtuale libero fra la .text e la sezione successiva:
        # crescere qui dentro non sposta NESSUNA RVA (solo i file offset)
        next_va = None
        for section in self.moved_sections:
            if next_va is None or section._zone_va < next_va:
                next_va = section._zone_va
        if next_va is None:
            next_va = self.text_va + align_up(self.text_vsize, self.section_alignment)
        self.max_growth = max(0, next_va - (self.text_va + self.text_vsize))
        self.added_bytes = 0

    def section_of(self, rva):
        for section in self.sections:
            if section._zone_va <= rva < section._zone_va + max(
                    section._zone_vs, section._zone_raw):
                return section
        return None

    def rva_to_off(self, rva):
        section = self.section_of(rva)
        if section is None:
            return None
        off = section._zone_pr + (rva - section._zone_va)
        if off < 0 or off >= len(self.data):
            return None
        return off

    def read(self, rva, size):
        off = self.rva_to_off(rva)
        if off is None or off + size > len(self.data):
            return None
        return bytes(self.data[off:off + size])

    def read_u32(self, rva):
        raw = self.read(rva, 4)
        return None if raw is None else struct.unpack("<I", raw)[0]

    def read_u64(self, rva):
        raw = self.read(rva, 8)
        return None if raw is None else struct.unpack("<Q", raw)[0]

    def in_image_rva(self, rva):
        return 0 <= rva < self.pe.OPTIONAL_HEADER.SizeOfImage

    # -- exception directory (.pdata) ------------------------------------
    def _parse_exception_directory(self):
        directory = self.pe.OPTIONAL_HEADER.DATA_DIRECTORY[3]
        if not directory.VirtualAddress or not directory.Size:
            return
        count = directory.Size // 12
        for index in range(count):
            entry_rva = directory.VirtualAddress + index * 12
            raw = self.read(entry_rva, 12)
            if raw is None:
                break
            begin, end, unwind = struct.unpack("<III", raw)
            if not (self.text_va <= begin < self.text_rva_end_vsize):
                continue
            info = self._parse_unwind_info(unwind & ~1)
            self.runtime_functions.append({
                "entry_rva": entry_rva, "begin": begin, "end": end,
                "unwind": unwind, "info": info,
            })
            if info is not None:
                prolog = info["prolog"]
                begin_end = min(end, begin + prolog)
                # il prologo e' descritto dall'unwind info: non va toccato
                self.no_resize_ranges.append((begin, begin_end))
                self.no_insert_ranges.append((begin, begin_end))
                if info["has_eh"] or info["chain"]:
                    self.no_resize_ranges.append((begin, end))
                    self.no_insert_ranges.append((begin, end))
                    self.eh_functions.append((begin, end))

    def _parse_unwind_info(self, rva):
        raw = self.read(rva, 4)
        if raw is None:
            return None
        version_flags, prolog, codes, frame_reg = raw[0], raw[1], raw[2], raw[3]
        version = version_flags & 7
        flags = version_flags >> 3
        if version not in (1, 2):
            return None
        code_bytes = self.read(rva + 4, codes * 2)
        if code_bytes is None:
            return None
        # l'handler RVA sta subito dopo gli unwind codes, allineato a 4
        handler_rva = None
        handler_off = rva + 4 + codes * 2
        if flags & 3:  # EHANDLER | UHANDLER
            handler_off = align_up(handler_off, 4)
            handler_rva = self.read_u32(handler_off)
        chain = None
        if flags & 4 and codes >= 1:
            # l'ultimo unwind code descrive un RUNTIME_FUNCTION concatenato
            chain_rva = rva + 4 + (codes - 1) * 2
            raw_chain = self.read(chain_rva, 12)
            if raw_chain:
                chain = struct.unpack("<III", raw_chain)
        return {
            "rva": rva, "version": version, "flags": flags, "prolog": prolog,
            "codes": codes, "frame_reg": frame_reg, "handler_rva": handler_rva,
            "handler_off": handler_off if (flags & 3) else None,
            "chain": chain, "chain_rva": (rva + 4 + (codes - 1) * 2) if chain else None,
            "has_eh": bool(flags & 1), "has_uh": bool(flags & 2),
        }

    # -- seeds ------------------------------------------------------------
    def _collect_seeds(self):
        seeds = []

        entry = self.pe.OPTIONAL_HEADER.AddressOfEntryPoint
        if self.text_va <= entry < self.text_rva_end_vsize:
            seeds.append(("entry", entry))

        for rtf in self.runtime_functions:
            seeds.append(("pdata", rtf["begin"]))
            info = rtf["info"]
            if info and info["chain"]:
                seeds.append(("pdata-chain", info["chain"][0]))
            if info and info["handler_rva"]:
                handler = info["handler_rva"]
                if self.text_va <= handler < self.text_rva_end_vsize:
                    seeds.append(("handler", handler))

        if hasattr(self.pe, "DIRECTORY_ENTRY_EXPORT"):
            for symbol in self.pe.DIRECTORY_ENTRY_EXPORT.symbols:
                if symbol.address and self.text_va <= symbol.address < self.text_rva_end_vsize:
                    seeds.append(("export", symbol.address))

        if hasattr(self.pe, "DIRECTORY_ENTRY_TLS"):
            tls = self.pe.DIRECTORY_ENTRY_TLS.struct
            array_rva = tls.AddressOfCallBacks
            for index in range(64):
                value = self.read_u64(array_rva + index * 8)
                if not value:
                    break
                rva = value - self.image_base
                if self.text_va <= rva < self.text_rva_end_vsize:
                    seeds.append(("tls", rva))

        if hasattr(self.pe, "DIRECTORY_ENTRY_BASERELOC"):
            for block in self.pe.DIRECTORY_ENTRY_BASERELOC:
                self._reloc_blocks = getattr(self, "_reloc_blocks", [])
                self._reloc_blocks.append(block)
                for entry in block.entries:
                    if entry.type != 10:          # solo DIR64
                        continue
                    value = self.read_u64(entry.rva)
                    if value is None:
                        continue
                    rva = value - self.image_base
                    if self.text_va <= rva < self.text_rva_end_vsize:
                        seeds.append(("reloc", rva))

        seen = set()
        for reason, rva in seeds:
            if rva in seen:
                continue
            seen.add(rva)
            if rva in self.insns:
                continue
            self.queue.append(rva)
            self.visits.add(rva)

    # -- recursive descent ------------------------------------------------
    def _decode_one(self, rva):
        raw = self.read(rva, 16)
        if not raw:
            return None
        for insn in self.cs.disasm(raw, rva, 1):
            return insn
        return None

    def _is_padding(self, rva):
        raw = self.read(rva, 16)
        if not raw:
            return True
        if len(raw) >= 4 and raw[:4] in (b"\xcc\xcc\xcc\xcc", b"\x00\x00\x00\x00"):
            return True
        return False

    def _branch_info(self, insn):
        """Ritorna (is_branch, is_cond, target) per i branch relativi."""
        groups = insn.groups
        if X86_GRP_CALL in groups and X86_INS_CALL == insn.id:
            if insn.operands and insn.operands[0].type == X86_OP_IMM:
                return False, False, None            # call: non termina il blocco
        if X86_GRP_JUMP in groups or (X86_GRP_BRANCH_RELATIVE in groups):
            if insn.operands and insn.operands[0].type == X86_OP_IMM:
                is_cond = insn.id != X86_INS_JMP
                return True, is_cond, insn.operands[0].imm
        return False, False, None

    def _disassemble(self):
        self._drain_queue()
        # ricorda tutti gli indirizzi di inizio istruzione
        self.code_rvas = set(self.insns)
        # inizi di funzione: entry point, .pdata, target delle call
        starts = {self.pe.OPTIONAL_HEADER.AddressOfEntryPoint}
        starts.update(rtf["begin"] for rtf in self.runtime_functions)
        for site, size, target, kind in self.branch_refs:
            if kind == "call" and target is not None:
                starts.add(target)
        self.function_starts = starts
        self.info("disassembly: %d istruzioni decodificate" % len(self.insns))

    def _decode_block(self, start):
        rva = start
        while True:
            if rva >= self.text_rva_end_vsize:
                return
            if rva in self.insns:
                return                                  # overlap: block splitting
            for lo, hi in self.jumptable_ranges:
                if lo <= rva < hi:
                    return                              # e' una jump table
            if self._is_padding(rva):
                return
            insn = self._decode_one(rva)
            if insn is None:
                return
            self.insns[rva] = insn
            self.visits.add(rva)
            next_rva = rva + insn.size

            is_branch, is_cond, target = self._branch_info(insn)
            groups = insn.groups
            if X86_GRP_CALL in groups and insn.id == X86_INS_CALL:
                # il target di una call e' codice: va accodato, altrimenti
                # le funzioni raggiunte solo per call restano "dati"
                if insn.operands and insn.operands[0].type == X86_OP_IMM:
                    call_target = insn.operands[0].imm
                    self.branch_refs.append((rva, insn.size, call_target, "call"))
                    self._queue_target(call_target)
                rva = next_rva
                continue
            if is_branch:
                self.branch_refs.append((rva, insn.size, target,
                                         "cond" if is_cond else "jmp"))
                self._queue_target(target)
                if not is_cond:
                    return
                rva = next_rva
                continue
            if insn.id in self.TERMINATORS:
                return
            if X86_GRP_RET in groups or X86_GRP_IRET in groups or X86_GRP_INT in groups:
                return
            rva = next_rva

    def _drain_queue(self):
        while self.queue:
            start = self.queue.pop()
            self._decode_block(start)

    def _purge_code_in_tables(self):
        """Toglie dalla mappa del codice le istruzioni dentro le jump table.

        Le tabelle possono essere riconosciute dopo che il resync ha
        decodificato qualcosa al loro interno: se restassero entrambe le
        rappresentazioni gli item si sovrapporrebbero e le patch delle
        entry scriverebbero dentro le istruzioni.
        """
        removed = 0
        for start, end in self.jumptable_ranges:
            for rva in [rva for rva in self.insns if start <= rva < end]:
                del self.insns[rva]
                removed += 1
        if removed:
            self.info("rimosse %d istruzioni dentro le jump table" % removed)
        return removed

    def _probe_gap_starts(self):
        """Ricerca un blocco valido subito dopo un errore di decodifica.

        Quando capstone non decodifica un byte (o si incontra padding in
        mezzo) il blocco si interrompe e il resto della funzione resta
        "dati".  Qui si prova ogni offset all'interno del buco, ma solo
        subito dopo del padding (CC/00/NOP) e solo se il blocco decodifica
        per intero e termina: il codice trovato viene ricollocato ma non
        obfuscato.
        """
        found = 0
        for gap_start, gap_end in self._text_gaps():
            if gap_end - gap_start < 4:
                continue
            for offset in range(0, min(16, gap_end - gap_start)):
                target = gap_start + offset
                if target in self.insns:
                    continue
                if offset and not self._is_padding(target - 1):
                    continue
                if self._probe_risky_block(target, limit=gap_end - target):
                    found += 1
                    break
        if found:
            self.info("resync nei buchi: %d blocchi recuperati" % found)
            self._drain_queue()
        return found

    # -- risky references (come binprotect) ------------------------------
    def _probe_risky_block(self, target, limit=0x400):
        """Prova a decodificare un blocco a `target`.

        Accetta solo se decodifica per intero, resta dentro `limit` byte e
        termina con un'istruzione di terminazione: e' il controllo che
        binprotect fa sulle "risky references" (target di `lea` che possono
        essere sia codice sia dati).
        """
        if target in self.insns:
            return False
        if self._is_padding(target):
            return False
        # una jump table riconosciuta non e' codice
        for lo, hi in self.jumptable_ranges:
            if lo <= target < hi:
                return False
        rva = target
        total = 0
        instructions = []
        while total < limit:
            insn = self._decode_one(rva)
            if insn is None:
                return False
            instructions.append(insn)
            rva += insn.size
            total += insn.size
            if insn.id in self.TERMINATORS or X86_GRP_RET in insn.groups:
                break
            if insn.id == X86_INS_JMP or X86_GRP_JUMP in insn.groups:
                break
            if rva >= self.text_rva_end_vsize:
                return False
        else:
            return False
        last = instructions[-1]
        terminates = (last.id in self.TERMINATORS or X86_GRP_RET in last.groups
                      or last.id == X86_INS_JMP or X86_GRP_JUMP in last.groups)
        if not terminates:
            return False
        # se il blocco finisce con un salto condizionale, il fallthrough e'
        # codice a tutti gli effetti: va accodato
        if (last.id != X86_INS_JMP
                and (X86_GRP_JUMP in last.groups
                     or X86_GRP_BRANCH_RELATIVE in last.groups)):
            self._queue_target(rva)
        # un blocco che finisce dentro un'altra istruzione non e' codice
        for insn in instructions:
            if insn.address + insn.size > rva:
                return False
        for insn in instructions:
            self.insns[insn.address] = insn
            # i salti interni vanno accodati, altrimenti il loro target
            # resta "dati" e la copertura non arriva mai al 100%
            if (insn.operands and insn.operands[0].type == X86_OP_IMM
                    and (X86_GRP_JUMP in insn.groups
                         or X86_GRP_CALL in insn.groups
                         or X86_GRP_BRANCH_RELATIVE in insn.groups)):
                self._queue_target(insn.operands[0].imm)
        # codice "rischioso": viene ricollocato ma non obfuscato
        self.no_resize_ranges.append((target, rva))
        self.no_insert_ranges.append((target, rva))
        self.risky_blocks.append((target, rva))
        return True

    def _scan_risky_references(self):
        """Segue i riferimenti RIP dentro la .text non ancora decodificati."""
        found = 0
        candidates = set()
        for rva, insn in list(self.insns.items()):
            for operand in insn.operands:
                target = None
                if operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP:
                    target = insn.address + insn.size + operand.mem.disp
                elif (operand.type == X86_OP_IMM and insn.encoding.imm_size == 8
                      and operand.imm >= self.image_base):
                    target = operand.imm - self.image_base
                if target is None:
                    continue
                if not (self.text_va <= target < self.text_rva_end_vsize):
                    continue
                if target in self.insns:
                    continue
                candidates.add(target)
        for target in sorted(candidates):
            if self._probe_risky_block(target):
                found += 1
        if found:
            self.info("risky references: %d blocchi recuperati" % found)
            self._drain_queue()
        self.sizes_report["risky"] = self.sizes_report.get("risky", 0) + found
        return found

    def _text_gaps(self):
        """Regioni di .text non decodificate (candidati dati)."""
        gaps = []
        rva = self.text_va
        for start in sorted(self.insns):
            insn = self.insns[start]
            if start > rva:
                gaps.append((rva, start))
            rva = max(rva, start + insn.size)
        if rva < self.text_rva_end_vsize:
            gaps.append((rva, self.text_rva_end_vsize))
        return gaps

    def _scan_code_pointer_tables(self):
        """Trova array di RVA/VA a codice dentro la .text (jump table).

        Non si cerca il pattern del compilatore: si scandiscono i buchi con
        passo 4/8 e si accettano solo run di almeno due valori che puntano a
        codice decodificabile.  E' il "brute force" che usa anche binprotect
        per le tabelle non limitate.
        """
        found = 0
        new_seeds = []
        table_ranges = []
        for gap_start, gap_end in self._text_gaps():
            if gap_end - gap_start < 8:
                continue
            blob = self.read(gap_start, gap_end - gap_start) or b""
            for step, width, mode in ((4, 4, "rva"), (8, 8, "va")):
                run = []
                # le entry sono allineate in RVA, non rispetto al gap
                first = (-gap_start) % step
                for offset in range(first, len(blob) - (step - 1), step):
                    target = self._table_entry_target(blob, offset, width, mode)
                    if target is None:
                        if len(run) >= 2:
                            table_ranges.append(
                                (gap_start + run[0][0],
                                 gap_start + run[-1][0] + step, list(run)))
                        run = []
                        continue
                    run.append((offset, target, width, mode))
                if len(run) >= 2:
                    table_ranges.append((gap_start + run[0][0],
                                         gap_start + run[-1][0] + step, list(run)))

        for start, end, entries in table_ranges:
            new_entries = []
            for offset, target, width, mode in entries:
                site = start + offset
                if site in self.data_patch_sites:
                    continue
                self._note_patch(site, width, mode, target)
                new_entries.append((offset, target))
                new_seeds.append(target)
            if not new_entries:
                continue
            found += len(new_entries)
            self.jumptable_ranges.append((start, end))
            self.no_resize_ranges.append((start, end))
            self.no_insert_ranges.append((start, end))
            # eventuale codice decodificato dentro la tabella va rimosso:
            # altrimenti gli item si sovrappongono
            for rva in [rva for rva in self.insns if start <= rva < end]:
                del self.insns[rva]
        if found:
            self.info("tabelle di puntatori a codice: %d entry in %d tabelle"
                      % (found, len(table_ranges)))
            for target in new_seeds:
                self._queue_target(target)
            self._drain_queue()
        return found

    def _table_entry_target(self, blob, offset, width, mode):
        if width == 4:
            value = struct.unpack_from("<I", blob, offset)[0]
            target = value
        else:
            value = struct.unpack_from("<Q", blob, offset)[0]
            if value < self.image_base:
                return None
            target = value - self.image_base
        if not (self.text_va <= target < self.text_rva_end_vsize):
            return None
        if target in self.insns:
            return target
        if self._is_padding(target):
            return None
        return target if self._decode_one(target) is not None else None

    def _queue_target(self, target):
        if target is None:
            return
        if not (self.text_va <= target < self.text_rva_end_vsize):
            return
        if target in self.insns or target in self.visits:
            return
        self.visits.add(target)
        self.queue.append(target)

    # -- gap probe --------------------------------------------------------
    def _probe_code_gaps(self):
        """Recupera le funzioni leaf senza RUNTIME_FUNCTION.

        Un "leaf" non compare nella .pdata, quindi non e' un seed. Se non
        lo si scopre, i suoi riferimenti RIP-relative restano sbagliati
        quando il codice si sposta. Il probe accetta un gap solo se
        decodifica per intero e termina con un terminatore.
        """
        gaps = []
        rva = self.text_va
        for start in sorted(self.insns):
            if start > rva:
                gaps.append((rva, start))
            rva = max(rva, start + self.insns[start].size)
        if rva < self.text_rva_end_vsize:
            gaps.append((rva, self.text_rva_end_vsize))

        accepted = 0
        for gap_start, gap_end in gaps:
            if gap_end - gap_start < 2 or gap_end - gap_start > 0x800:
                continue
            if self._is_padding(gap_start):
                continue
            instructions = []
            rva = gap_start
            ok = True
            while rva < gap_end:
                if rva in self.insns:
                    ok = False
                    break
                insn = self._decode_one(rva)
                if insn is None:
                    ok = False
                    break
                instructions.append(insn)
                rva += insn.size
            if not ok or rva != gap_end or not instructions:
                continue
            last = instructions[-1]
            groups = last.groups
            terminates = (last.id in self.TERMINATORS or X86_GRP_RET in groups
                          or X86_GRP_IRET in groups)
            if not terminates:
                continue
            for insn in instructions:
                self.insns[insn.address] = insn
            accepted += 1
            # un blocco "provato" non si modifica: non conosciamo la funzione
            self.no_resize_ranges.append((gap_start, gap_end))
            self.no_insert_ranges.append((gap_start, gap_end))
        self.code_rvas = set(self.insns)
        if accepted:
            self.info("gap probe: %d blocchi di codice recuperati" % accepted)

    # -- jump table -------------------------------------------------------
    def _find_jump_tables(self):
        """Trova le jump table dentro la .text (MSVC, LLVM, GCC)."""
        table_entries = {}
        insns_sorted = sorted(self.insns)
        index_of = {rva: i for i, rva in enumerate(insns_sorted)}

        for rva in insns_sorted:
            insn = self.insns[rva]
            if insn.id != X86_INS_JMP:
                continue
            if not insn.operands:
                continue
            operand = insn.operands[0]
            if operand.type != X86_OP_REG:
                continue
            # risali al massimo 12 istruzioni cercando un lea rip-relative
            # oppure un mov di un indirizzo assoluto
            position = index_of[rva]
            table_base = None
            for step in range(1, 13):
                if position - step < 0:
                    break
                prev = self.insns[insns_sorted[position - step]]
                if prev.id in (X86_INS_RET, X86_INS_INT3):
                    break
                if "lea" in prev.mnemonic and prev.operands:
                    if not prev.operands:
                        continue
                    mem = prev.operands[-1]
                    if mem.type == X86_OP_MEM and mem.mem.base == X86_REG_RIP:
                        table_base = prev.address + prev.size + mem.mem.disp
                        break
                if prev.mnemonic == "mov" and len(prev.operands) == 2:
                    dst, src = prev.operands
                    if dst.type == X86_OP_REG and src.type == X86_OP_IMM:
                        value = src.imm
                        if self.image_base <= value < self.image_base + self.pe.OPTIONAL_HEADER.SizeOfImage:
                            table_base = value - self.image_base
                            break
            if table_base is None:
                continue
            if not (self.text_va <= table_base < self.text_rva_end_vsize):
                continue
            # controlla che una delle istruzioni vicine usi un indice scalato
            scaled = False
            for step in range(1, 13):
                if position - step < 0:
                    break
                prev = self.insns[insns_sorted[position - step]]
                for op in prev.operands:
                    if op.type == X86_OP_MEM and op.mem.index not in (0, X86_REG_RIZ):
                        if op.mem.scale in (4, 8):
                            scaled = True
                if scaled:
                    break
            if not scaled:
                continue

            entry_size = 4
            if self.read_u32(table_base) is None:
                continue
            entries = []
            rva_entry = table_base
            for _ in range(self.MAX_JMPTABLE):
                raw = self.read(rva_entry, entry_size)
                if raw is None:
                    break
                value = struct.unpack("<i", raw)[0]
                mode, target = self._resolve_jumptable_entry(rva_entry, table_base, value)
                if mode is None:
                    break
                entries.append((rva_entry, mode, target))
                rva_entry += entry_size
            if len(entries) < 2:
                continue
            self.jump_tables.append({
                "base": table_base, "entries": entries, "index": rva,
            })
            start = table_base
            end = rva_entry
            self.jumptable_ranges.append((start, end))
            self.no_resize_ranges.append((start, end))
            self.no_insert_ranges.append((start, end))
            for entry_rva, mode, target in entries:
                table_entries[entry_rva] = (mode, target)
                self._queue_target(target)

        self.jumptable_entries = table_entries
        if self.jump_tables:
            self.info("jump table: %d tabelle, %d entry"
                      % (len(self.jump_tables), len(table_entries)))

    def _resolve_jumptable_entry(self, entry_rva, table_base, value):
        """Capisce se l'entry e' una RVA assoluta o un offset relativo."""
        if not -(2 ** 31) <= value < 2 ** 31:
            return None, None
        candidates = [
            ("abs", value),
            ("rel-entry", entry_rva + value),
            ("rel-base", table_base + value),
        ]
        for mode, target in candidates:
            if target in self.insns:
                return mode, target
        # un target valido ma non ancora decodificato e' accettabile
        for mode, target in candidates:
            if self.text_va <= target < self.text_rva_end_vsize:
                probe = self._decode_one(target)
                if probe is not None and target not in self.visits:
                    return mode, target
        return None, None

    # -- costruzione del layout ------------------------------------------
    def _merge_ranges(self, ranges):
        if not ranges:
            return []
        ranges = sorted(ranges)
        merged = [list(ranges[0])]
        for start, end in ranges[1:]:
            if start <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], end)
            else:
                merged.append([start, end])
        return [tuple(r) for r in merged]

    def _build_items(self):
        self.no_resize_ranges = self._merge_ranges(self.no_resize_ranges)
        self.no_insert_ranges = self._merge_ranges(self.no_insert_ranges)

        rva = self.text_va
        while rva < self.text_end_old:
            insn = self.insns.get(rva)
            if insn is not None:
                item = Instruction("insn", rva, insn.size, bytes(insn.bytes))
                item.cs_insn = insn
                item.original_instruction = insn
                item.old_instruction = insn
                item.address_history = [rva]
                self._annotate(item, insn)
                self.items.append(item)
                rva += insn.size
                continue
            next_start = self._next_insn_start(rva)
            if next_start is None or next_start <= rva:
                next_start = self.text_end_old
            # spezza i blocchi dati sui confini delle jump table: cosi' una
            # tabella e' un item a se' e la copertura la riconosce
            for table_start, table_end in self.jumptable_ranges:
                if rva < table_start < next_start:
                    next_start = table_start
                    break
                if rva <= table_start < next_start and table_start == rva:
                    next_start = min(next_start, table_end)
                    break
            raw = self.read(rva, next_start - rva) or b""
            item = Instruction("data", rva, len(raw), raw)
            for table_start, table_end in self.jumptable_ranges:
                if table_start <= rva and rva + len(raw) <= table_end:
                    item.role = "table"
                    break
            self.items.append(item)
            rva += len(raw) if raw else 1

        # la coda raw che sta oltre VirtualSize viaggia con gli item
        while rva < self.text_end_old:
            raw = self.read(rva, self.text_end_old - rva) or b""
            self.items.append(Instruction("data", rva, len(raw), raw))
            rva += len(raw) or 1

        self.item_starts = [item.old_rva for item in self.items]
        # annota i riferimenti per ogni istruzione
        for item in self.items:
            if item.kind != "insn":
                continue
            self._attach_refs(item)

    def _next_insn_start(self, rva):
        position = bisect.bisect_left(self.code_starts, rva)
        if position < len(self.code_starts):
            return self.code_starts[position]
        return None

    @property
    def code_starts(self):
        if not hasattr(self, "_code_starts"):
            self._code_starts = sorted(self.insns)
        return self._code_starts

    def _annotate(self, item, insn):
        item.opcode = insn.bytes[insn.encoding.imm_offset - 1] if insn.encoding.imm_offset else None
        item.imm_off = insn.encoding.imm_offset
        item.imm_size = insn.encoding.imm_size
        item.disp_off = insn.encoding.disp_offset
        item.disp_size = insn.encoding.disp_size

    def _attach_refs(self, item):
        insn = item.cs_insn
        is_branch, is_cond, target = self._branch_info(insn)
        if is_branch and target is not None:
            item.is_branch = True
            item.is_cond = is_cond
            item.is_uncond = not is_cond
            item.target_old = target
            if item.imm_size not in (1, 4):
                item.is_branch = False
            return
        if X86_GRP_CALL in insn.groups and insn.id == X86_INS_CALL:
            if insn.operands and insn.operands[0].type == X86_OP_IMM:
                item.is_branch = True
                item.is_cond = False
                item.is_uncond = False
                item.target_old = insn.operands[0].imm
                return
        for operand in insn.operands:
            if operand.type == X86_OP_MEM:
                if operand.mem.base == X86_REG_RIP:
                    # in x64 con base RIP il displacement e' SEMPRE disp32.
                    # capstone su alcune codifiche SSE riporta disp_size 2/1:
                    # non ci si puo' fidare, si usa l'offset reale.
                    item.disp_off = (insn.encoding.disp_offset
                                     or (insn.size - 4))
                    item.disp_size = 4
                    item.rip_target = insn.address + insn.size + operand.mem.disp
                    return
                if (operand.mem.base == 0 and operand.mem.index in (0, X86_REG_RIZ)):
                    value = operand.mem.disp & 0xFFFFFFFF
                    if value in self.insns or value in self.jumptable_entries:
                        item.abs_target = value
                        item.abs_size = 4
                        item.abs_va = False
                        item.abs_is_mem = True
                        item.disp_off = insn.encoding.disp_offset or (insn.size - 4)
                continue
            if operand.type == X86_OP_IMM and item.imm_size in (4, 8):
                value = operand.imm & 0xFFFFFFFFFFFFFFFF
                if item.imm_size == 8 and value >= self.image_base:
                    rva = value - self.image_base
                    if rva in self.insns or rva in self.jumptable_entries:
                        item.abs_target = rva
                        item.abs_size = 8
                        item.abs_va = True
                        return
                if (item.imm_size == 4 and insn.mnemonic == "mov"
                        and insn.operands[0].type == X86_OP_REG):
                    # un imm32 che vale esattamente l'inizio di una funzione
                    # e' un puntatore a codice (binari senza relocation)
                    rva = value & 0xFFFFFFFF
                    if rva in self.function_starts:
                        item.abs_target = rva
                        item.abs_size = 4
                        item.abs_va = False
                        return

    # -- riferimenti PE (raccolta) ---------------------------------------
    def _note_patch(self, site_rva, width, mode, target=None, constant=None):
        self.patches.append((site_rva, width, mode, target, constant))
        self.data_patch_sites.add(site_rva)
        return

    def _parse_data_refs(self):
        self._parse_relocations()
        self._parse_unwind_refs()
        self._parse_imports()
        self._parse_exports()
        self._parse_resources()
        self._parse_debug()
        self._parse_tls()
        self._parse_load_config()
        self._parse_delay_imports()
        self._parse_scope_tables()
        self._parse_cpp_eh()
        self._parse_data_pointers()

    def _parse_relocations(self):
        if not hasattr(self.pe, "DIRECTORY_ENTRY_BASERELOC"):
            return
        count = 0
        for block in self.pe.DIRECTORY_ENTRY_BASERELOC:
            block_rva = block.struct.VirtualAddress
            if block_rva:
                self._note_patch(self._field_rva(block.struct, "VirtualAddress"),
                                 4, "rva", block_rva)
            for entry in block.entries:
                if entry.type == 0:
                    continue
                if entry.type == 10:
                    width = 8
                elif entry.type == 3:
                    width = 4
                else:
                    continue
                value = (self.read_u64(entry.rva) if width == 8
                         else self.read_u32(entry.rva))
                if value is None:
                    continue
                target = value - self.image_base if width == 8 else value
                if not self.in_image_rva(target):
                    continue
                self._note_patch(entry.rva, width, "va" if width == 8 else "rva", target)
                count += 1
        self.sizes_report["reloc"] = count

    def _field_rva(self, struct_obj, field):
        """File offset -> RVA per un campo di una struttura PE."""
        try:
            offset = struct_obj.dump_dict()[field]["FileOffset"]
        except Exception:
            return None
        return self.off_to_rva(offset)

    def off_to_rva(self, offset):
        if offset is None:
            return None
        for section in self.sections:
            if section._zone_pr <= offset < section._zone_pr + section._zone_raw:
                return section._zone_va + (offset - section._zone_pr)
        return offset

    def _parse_unwind_refs(self):
        count = 0
        for rtf in self.runtime_functions:
            raw = self.read(rtf["entry_rva"], 12)
            if raw is None:
                continue
            begin, end, unwind = struct.unpack("<III", raw)
            self._note_patch(rtf["entry_rva"], 4, "rva", begin)
            # la fine dipende dalla permutazione dei blocchi (-ibp)
            self._note_patch(rtf["entry_rva"] + 4, 4, "func-end", end,
                             constant=begin)
            self._note_patch(rtf["entry_rva"] + 8, 4, "rva-plain", unwind & ~1)
            count += 1
            info = rtf["info"]
            if not info:
                continue
            if info["handler_rva"]:
                self._note_patch(info["handler_off"], 4, "rva", info["handler_rva"])
            if info["chain"]:
                base = info["chain_rva"]
                self._note_patch(base, 4, "rva", info["chain"][0])
                self._note_patch(base + 4, 4, "func-end", info["chain"][1],
                                 constant=info["chain"][0])
                self._note_patch(base + 8, 4, "rva-plain", info["chain"][2] & ~1)
        self.sizes_report["unwind"] = count

    def _parse_imports(self):
        if not hasattr(self.pe, "DIRECTORY_ENTRY_IMPORT"):
            return
        count = 0
        for descriptor in self.pe.DIRECTORY_ENTRY_IMPORT:
            struct_obj = descriptor.struct
            for field in ("OriginalFirstThunk", "Name", "FirstThunk"):
                rva = self._field_rva(struct_obj, field)
                value = getattr(struct_obj, field, 0)
                if rva and value:
                    self._note_patch(rva, 4, "rva", value)
                    count += 1
            # le entry della ILT (e della IAT non ancora risolta) contengono
            # la RVA della Hint/Name: se non si aggiornano il loader non
            # risolve piu' l'import (STATUS_ENTRYPOINT_NOT_FOUND)
            ilt = struct_obj.OriginalFirstThunk or struct_obj.FirstThunk
            iat = struct_obj.FirstThunk
            for index in range(0x10000):
                value = self.read_u64(ilt + index * 8)
                if not value:
                    break
                if value & 0x8000000000000000:
                    continue                       # import per ordinale
                target = value & 0xFFFFFFFF
                if not self.in_image_rva(target):
                    break
                self._note_patch(ilt + index * 8, 8, "rva64", target)
                if self.read_u64(iat + index * 8) == value:
                    self._note_patch(iat + index * 8, 8, "rva64", target)
                count += 1
        self.sizes_report["import"] = count

    def _parse_exports(self):
        if not hasattr(self.pe, "DIRECTORY_ENTRY_EXPORT"):
            return
        export = self.pe.DIRECTORY_ENTRY_EXPORT
        struct_obj = export.struct
        for field in ("Name", "AddressOfFunctions", "AddressOfNames",
                      "AddressOfNameOrdinals"):
            rva = self._field_rva(struct_obj, field)
            value = getattr(struct_obj, field, 0)
            if rva and value:
                self._note_patch(rva, 4, "rva", value)
        for index in range(getattr(struct_obj, "NumberOfFunctions", 0)):
            site = struct_obj.AddressOfFunctions + index * 4
            target = self.read_u32(site)
            if target:
                self._note_patch(site, 4, "rva", target)
        for index in range(getattr(struct_obj, "NumberOfNames", 0)):
            site = struct_obj.AddressOfNames + index * 4
            target = self.read_u32(site)
            if target:
                self._note_patch(site, 4, "rva", target)
            site = struct_obj.AddressOfNameOrdinals + index * 2
            # gli ordinali sono costanti: nessuna patch

    def _parse_resources(self):
        if not hasattr(self.pe, "DIRECTORY_ENTRY_RESOURCE"):
            return
        directory_rva = self.pe.OPTIONAL_HEADER.DATA_DIRECTORY[2].VirtualAddress

        def walk(rva, depth):
            if depth > 3:
                return
            raw = self.read(rva, 16)
            if raw is None:
                return
            named, ids = struct.unpack("<HH", raw[:4])
            count = named + ids
            for index in range(count):
                entry_rva = rva + 16 + index * 8
                entry = self.read(entry_rva, 8)
                if entry is None:
                    return
                name, offset = struct.unpack("<II", entry)
                if offset & 0x80000000:
                    walk(directory_rva + (offset & 0x7FFFFFFF), depth + 1)
                else:
                    data_rva = rva + offset
                    data_entry = self.read(data_rva, 16)
                    if data_entry is None:
                        continue
                    data_offset, size = struct.unpack("<II", data_entry[:8])
                    if data_offset:
                        self._note_patch(data_rva, 4, "rva", data_offset)

        if directory_rva:
            walk(directory_rva, 0)

    def _data_directory_site(self, index):
        """Offset di file del campo VirtualAddress della directory."""
        optional = self.pe.OPTIONAL_HEADER
        base = optional.get_file_offset()
        base += 112 if optional.Magic == 0x20B else 96
        return base + index * 8

    def _parse_debug(self):
        if not hasattr(self.pe, "DIRECTORY_ENTRY_DEBUG"):
            return
        for entry in self.pe.DIRECTORY_ENTRY_DEBUG:
            struct_obj = entry.struct
            site = self._field_rva(struct_obj, "AddressOfRawData")
            if site and struct_obj.AddressOfRawData:
                self._note_patch(site, 4, "rva", struct_obj.AddressOfRawData)
            # PointerToRawData e' un offset di file: lo spostamento dei file
            # offset e' pari a delta, quindi va trattato a parte
            site = self._field_rva(struct_obj, "PointerToRawData")
            if site and struct_obj.PointerToRawData:
                self._note_patch(site, 4, "fileoff", None,
                                 constant=struct_obj.PointerToRawData)

    def _parse_tls(self):
        if not hasattr(self.pe, "DIRECTORY_ENTRY_TLS"):
            return
        struct_obj = self.pe.DIRECTORY_ENTRY_TLS.struct
        for field in ("AddressOfIndex", "AddressOfCallBacks"):
            site = self._field_rva(struct_obj, field)
            value = getattr(struct_obj, field, 0)
            if site and value:
                self._note_patch(site, 4, "rva", value)
        callbacks = struct_obj.AddressOfCallBacks
        for index in range(64):
            site = callbacks + index * 8
            value = self.read_u64(site)
            if not value:
                break
            target = value - self.image_base
            if self.in_image_rva(target):
                self._note_patch(site, 8, "va", target)

    def _parse_load_config(self):
        if not hasattr(self.pe, "DIRECTORY_ENTRY_LOAD_CONFIG"):
            return
        struct_obj = self.pe.DIRECTORY_ENTRY_LOAD_CONFIG.struct
        va_fields = ("SecurityCookie", "SEHandlerTable",
                     "GuardCFCheckFunctionPointer", "GuardCFDispatchFunctionPointer",
                     "GuardCFFunctionTable", "GuardAddressTakenIatEntryTable",
                     "GuardLongJumpTargetTable", "DynamicValueRelocTable",
                     "CHPEMetadataPointer")
        for field in va_fields:
            site = self._field_rva(struct_obj, field)
            value = getattr(struct_obj, field, 0)
            if not site or not value:
                continue
            target = value - self.image_base
            if self.in_image_rva(target):
                self._note_patch(site, 8, "va", target)
        # tabelle di handler: array di RVA a 4 byte
        for field, count_field in (("SEHandlerTable", "SEHandlerCount"),
                                   ("GuardCFFunctionTable", "GuardCFFunctionCount")):
            value = getattr(struct_obj, field, 0)
            count = getattr(struct_obj, count_field, 0)
            if not value or not count or count > 0x10000:
                continue
            base = value - self.image_base
            for index in range(count):
                site = base + index * 4
                target = self.read_u32(site)
                if target:
                    self._note_patch(site, 4, "rva-unwind", target)

    def _parse_delay_imports(self):
        if not hasattr(self.pe, "DIRECTORY_ENTRY_DELAY_IMPORT"):
            return
        for descriptor in self.pe.DIRECTORY_ENTRY_DELAY_IMPORT:
            struct_obj = descriptor.struct
            for field in ("DllNameRVA", "ModuleHandleRVA", "ImportAddressTableRVA",
                          "ImportNameTableRVA", "BoundImportAddressTableRVA",
                          "UnloadInformationTableRVA"):
                site = self._field_rva(struct_obj, field)
                value = getattr(struct_obj, field, 0)
                if site and value:
                    self._note_patch(site, 4, "rva", value)

    def _parse_scope_tables(self):
        """C_SCOPE_TABLE: dati del __C_specific_handler, puntati dall'unwind."""
        count = 0
        for rtf in self.runtime_functions:
            info = rtf["info"]
            if not info or not info.get("handler_rva"):
                continue
            if info["has_eh"] is False and info["has_uh"] is False:
                continue
            table_rva = self.read_u32(info["handler_off"] + 4)
            if table_rva is None:
                continue
            raw = self.read(table_rva, 4)
            if raw is None:
                continue
            entries = struct.unpack("<I", raw)[0]
            if entries > 0x1000:
                continue
            plausible = True
            for index in range(entries):
                site = table_rva + 4 + index * 16
                entry = self.read(site, 16)
                if entry is None:
                    plausible = False
                    break
                begin, end, handler, target = struct.unpack("<IIII", entry)
                if not (self.text_va <= begin < self.text_rva_end_vsize):
                    plausible = False
                    break
                if not (self.text_va <= end <= self.text_rva_end_vsize):
                    plausible = False
                    break
            if not plausible:
                continue
            self._note_patch(info["handler_off"] + 4, 4, "rva-plain", table_rva)
            for index in range(entries):
                site = table_rva + 4 + index * 16
                begin, end, handler, target = struct.unpack("<IIII", self.read(site, 16))
                self._note_patch(site, 4, "rva", begin)
                self._note_patch(site + 4, 4, "rva-boundary", end)
                if self.in_image_rva(handler) and handler > 0x10000:
                    self._note_patch(site + 8, 4, "rva", handler)
                self._note_patch(site + 12, 4, "rva", target)
                count += 1
        self.sizes_report["scope"] = count

    def _parse_cpp_eh(self):
        """FuncInfo3/FuncInfo4: cerca il magic nelle sezioni dati.

        Non riscrivo gli offset interni alla funzione (ip2state, unwind map),
        perche' le funzioni con handler non vengono modificate.  Riscrivo
        solo le RVA contenute nelle strutture.
        """
        for magic, label in ((0x19930520, "FH3"), (0x19930521, "FH4"),
                             (0x19930522, "FH4")):
            pattern = struct.pack("<I", magic)
            for section in self.moved_sections:
                base = section._zone_va
                blob = self.read(base, section._zone_vs) or b""
                start = 0
                while True:
                    index = blob.find(pattern, start)
                    if index < 0:
                        break
                    start = index + 1
                    self.cpp_eh_found += 1
                    self.eh_structures.append((base + index, label))
        if self.cpp_eh_found:
            self.info("C++ EH: %d FuncInfo trovate" % self.cpp_eh_found)

    def _parse_data_pointers(self):
        """Puntatori assoluti nei dati che puntano a codice.

        Con le relocation presenti questo passo e' ridondante ma innocuo;
        senza relocation e' l'unico modo per seguire le tabelle di puntatori.
        """
        patched = 0
        for section in self.moved_sections:
            base = section._zone_va
            size = section._zone_vs & ~7
            for offset in range((-base) % 8, size - 8, 8):
                site = base + offset
                if site in self.data_patch_sites:
                    continue
                value = self.read_u64(site)
                if value is None or value < self.image_base:
                    continue
                target = value - self.image_base
                if target in self.insns:
                    self._note_patch(site, 8, "va", target)
                    patched += 1
        self.sizes_report["data-ptr"] = patched

    def _scan_data_code_tables(self):
        """Tabelle di RVA a codice nelle sezioni dati (memset, switch, ...).

        Esempio reale (memset AVX2 di ploader.exe):
            mov r11d, dword ptr [r10 + r11*4 + 0x216d0]
            add  r11, r10
            jmp  r11
        Le entry stanno in .rdata e contengono RVA assolute: se il codice si
        sposta vanno riscritte *e* i target vanno disassemblati, altrimenti i
        loro riferimenti RIP-relative restano sbagliati.  Si accettano solo
        run di almeno due valori che puntano a codice, per non toccare le
        costanti.
        """
        found = 0
        new_seeds = []
        for section in self.moved_sections:
            base = section._zone_va
            size = section._zone_vs
            blob = self.read(base, size) or b""
            for step, width, mode in ((4, 4, "rva"), (8, 8, "va")):
                run = []
                for offset in range((-base) % step, len(blob) - (step - 1), step):
                    site = base + offset
                    if width == 4:
                        target = struct.unpack_from("<I", blob, offset)[0]
                    else:
                        value = struct.unpack_from("<Q", blob, offset)[0]
                        target = (value - self.image_base
                                  if value >= self.image_base else None)
                    ok = (target is not None
                          and self.text_va <= target < self.text_rva_end_vsize
                          and (target in self.insns
                               or self._decode_one(target) is not None))
                    if not ok:
                        found += self._flush_table_run(run, width, mode, new_seeds)
                        run = []
                        continue
                    run.append((site, target))
                found += self._flush_table_run(run, width, mode, new_seeds)
        if found:
            self.info("tabelle nei dati: %d puntatori a codice" % found)
            for target in new_seeds:
                self._queue_target(target)
            self._drain_queue()
        self.sizes_report["data-tables"] = self.sizes_report.get("data-tables", 0) + found
        return found

    def _flush_table_run(self, run, width, mode, seeds):
        if len(run) < 2:
            return 0
        added = 0
        for site_rva, target_rva in run:
            seeds.append(target_rva)
            if site_rva in self.data_patch_sites:
                continue
            self._note_patch(site_rva, width, mode, target_rva)
            added += 1
        return added

    # -- map --------------------------------------------------------------
    def map_point(self, old_rva):
        """Vecchia RVA -> nuova RVA."""
        if old_rva is None:
            return None
        if self.text_va <= old_rva < self.text_end_old:
            position = bisect.bisect_right(self.old_keys, old_rva) - 1
            if position < 0:
                return old_rva + self.delta
            item = self.items[self.old_index[position]]
            return item.new_rva + (old_rva - item.old_rva)
        if old_rva == self.text_end_old:
            if not self.items:
                return old_rva + self.delta
            last = self.items[-1]
            return last.new_rva + last.size
        section = self.section_of(old_rva)
        if section is not None and section._zone_va > self.text_va:
            return old_rva + self.delta
        return old_rva

    def repair_target(self, old_target):
        if old_target is None:
            return None
        if self.in_image_rva(old_target):
            return self.map_point(old_target)
        return old_target

    # -- layout -----------------------------------------------------------
    def _assign_rvas(self):
        rva = self.text_va
        for item in self.items:
            item.new_rva = rva
            rva += item.size
        content_end = rva
        inserted = content_end - self.text_end_old
        if inserted < 0:
            raise ZoneError("layout piu' corto dell'originale (%d)" % inserted)
        if inserted > self.max_growth and self.growth_mode == "slack":
            raise ZoneError(
                "servono %d byte ma lo spazio libero prima della sezione "
                "successiva e' %d: riduci le inserzioni o usa --grow=shift"
                % (inserted, self.max_growth))
        self.inserted_total = inserted
        if self.growth_mode == "slack":
            # nessuna RVA cambia: cresce solo la parte raw della .text
            content = self.text_end_old - self.text_va + inserted
            raw_new = max(self.text_raw_size,
                          align_up(content, self.file_alignment))
            self.delta = 0
            self.raw_delta = raw_new - self.text_raw_size
        else:
            new_delta = align_up(inserted, self.section_alignment) if inserted else 0
            self.delta = new_delta
            self.raw_delta = new_delta
            raw_new = self.text_raw_size + new_delta
        changed = self.delta != getattr(self, "_last_delta", None)
        self._last_delta = self.delta
        self.text_content_new_size = content_end - self.text_va
        self.text_pad_new = raw_new - self.text_content_new_size
        if self.text_pad_new < 0:
            raise ZoneError("padding negativo")
        # indice old_rva -> item, ricostruito ad ogni layout.
        # Dopo -ibp l'ordine di emissione non coincide piu' con l'ordine
        # degli indirizzi: la mappa va ordinata sulle RVA vecchie.
        pairs = [(item.old_rva, index) for index, item in enumerate(self.items)
                 if item.old_rva is not None]
        pairs.sort()
        self.old_keys = [pair[0] for pair in pairs]
        self.old_index = [pair[1] for pair in pairs]
        self.function_end = self._compute_function_end()
        return changed

    def _compute_function_end(self):
        """Nuova fine di ogni funzione .pdata dopo una permutazione.

        Se i blocchi di una funzione vengono mischiati la funzione resta
        contigua, ma `EndAddress` non e' piu' l'immagine della vecchia fine:
        va preso il massimo fine fra gli item della funzione.
        """
        if not self.permuted:
            return {}
        functions = sorted(self.runtime_functions, key=lambda f: f["begin"])
        begins = [f["begin"] for f in functions]
        ends = {}
        for item in self.items:
            if item.old_rva is None:
                continue
            position = bisect.bisect_right(begins, item.old_rva) - 1
            if position < 0:
                continue
            function = functions[position]
            if not (function["begin"] <= item.old_rva < function["end"]):
                continue
            end = item.new_rva + item.size
            if end > ends.get(function["begin"], 0):
                ends[function["begin"]] = end
        return ends

    def _prepare_item(self, item):
        """Calcola i byte finali; ritorna True se serve piu' spazio."""
        # i branch vengono codificati qualunque sia la loro origine
        # (istruzione originale, trampolino di -ebi, connettore di -ibp)
        if item.is_branch and item.imm_size:
            encoded = self._encode_branch(item)
            if len(encoded) > item.size:
                item.size = len(encoded)
                return True
            item.new_bytes = encoded + b"\x90" * (item.size - len(encoded))
            return False
        if item.kind == "data":
            item.new_bytes = item.data
            return False
        if item.kind == "seq":
            item.new_bytes = item.data
            return False
        if item.replacement is not None:
            if len(item.replacement) > item.size:
                item.size = len(item.replacement)
                item.new_bytes = item.replacement
                return True
            # se la forma nuova e' piu' corta si riempie di nop: cosi' il
            # layout resta stabile e nessuna istruzione si sposta
            item.new_bytes = item.replacement + b"\x90" * (
                item.size - len(item.replacement))
            return False
        if item.is_branch:
            encoded = self._encode_branch(item)
            if len(encoded) > item.size:
                item.size = len(encoded)
                return True
            item.new_bytes = encoded + b"\x90" * (item.size - len(encoded))
            return False
        if item.rip_target is not None:
            target = self.repair_target(item.rip_target)
            disp = target - (item.new_rva + item.size)
            raw = bytearray(item.orig_bytes)
            if not -(2 ** 31) <= disp < 2 ** 31:
                raise ZoneError("disp32 fuori range a %#x" % item.old_rva)
            struct.pack_into("<i", raw, item.disp_off, disp)
            item.new_bytes = bytes(raw)
            return False
        if item.abs_target is not None:
            target = self.repair_target(item.abs_target)
            raw = bytearray(item.orig_bytes)
            enc = item.cs_insn.encoding
            if item.abs_size == 8:
                value = target + self.image_base if item.abs_va else target
                struct.pack_into("<Q", raw, enc.imm_offset, value)
            elif item.abs_is_mem:
                struct.pack_into("<I", raw, item.disp_off, target & 0xFFFFFFFF)
            else:
                struct.pack_into("<I", raw, enc.imm_offset, target & 0xFFFFFFFF)
            item.new_bytes = bytes(raw)
            return False
        item.new_bytes = item.orig_bytes
        return False

    def _encode_branch(self, item):
        """Codifica il branch con il target nuovo.

        Se la codifica attuale non basta (rel8 fuori range) passa alla forma
        lunga e aggiorna item.size: il chiamante rilancia il layout.
        """
        target = self.repair_target(item.target_old)
        if item.target_item is not None:
            target = item.target_item.new_rva
        if target is None:
            return item.orig_bytes
        imm_size = item.imm_size
        raw = bytearray(item.orig_bytes)
        if item.size == item.orig_size and imm_size == 4:
            disp = target - (item.new_rva + item.size)
            if not -(2 ** 31) <= disp < 2 ** 31:
                raise ZoneError("rel32 fuori range a %#x" % item.old_rva)
            struct.pack_into("<i", raw, item.imm_off, disp)
            return bytes(raw)
        if item.size == item.orig_size and imm_size == 1:
            disp = target - (item.new_rva + item.size)
            if -128 <= disp <= 127:
                struct.pack_into("<b", raw, item.imm_off, disp)
                return bytes(raw)
        # forma lunga
        opcode = raw[item.imm_off - 1] if item.imm_off else 0
        prefix = bytes(raw[:max(0, item.imm_off - 1)])
        if opcode == 0xEB:                          # jmp short -> jmp near
            new = b"\xe9" + p32(target - (item.new_rva + 5))
        elif 0x70 <= opcode <= 0x7F:                # jcc short -> jcc near
            new = bytes([0x0F, 0x80 + (opcode - 0x70)]) + p32(
                target - (item.new_rva + 6))
        elif opcode in (0xE0, 0xE1, 0xE2, 0xE3):    # loop / jrcxz
            trampoline = prefix + bytes([opcode, 0x05])
            new = trampoline + b"\xe9" + p32(
                target - (item.new_rva + len(trampoline) + 5))
        elif opcode in (0xE8, 0xE9):
            new = bytes([opcode]) + p32(target - (item.new_rva + 5))
        elif opcode == 0x0F and item.imm_size == 4:
            new = bytes(raw[:2]) + p32(target - (item.new_rva + 6))
        else:
            raise ZoneError("branch non allargabile a %#x (opcode %#x)"
                            % (item.old_rva, opcode))
        return new

    def _layout(self, max_iterations=60):
        for item in self.items:
            item.reset_size()
        for iteration in range(max_iterations):
            delta_changed = self._assign_rvas()
            growth = False
            for item in self.items:
                if self._prepare_item(item):
                    growth = True
            if not growth and not delta_changed:
                self._assign_rvas()
                for item in self.items:
                    if self._prepare_item(item):
                        raise ZoneError("layout non convergente")
                return iteration + 1
        raise ZoneError("layout non convergente dopo %d iterazioni" % max_iterations)

    # -- emissione --------------------------------------------------------
    def _fit_growth(self):
        """Riduce le inserzioni finche' il layout entra nello spazio libero.

        L'allargamento dei branch rel8 -> rel32 dipende dal layout, quindi il
        budget stimato a priori non basta: si toglie qualche sequenza e si
        ricalcola.
        """
        for _ in range(60):
            try:
                self._layout()
                return
            except ZoneError as error:
                if not str(error).startswith("servono"):
                    raise
                if self.growth_mode != "slack":
                    raise
                seqs = [index for index, item in enumerate(self.items)
                        if item.kind == "seq" and item.role in (None, "nop", "bcf")]
                if not seqs:
                    raise
                drop = set(seqs[max(0, len(seqs) // 8):])
                before = len(self.items)
                self.items = [item for index, item in enumerate(self.items)
                              if index not in drop]
                self.info("riduco le inserzioni: %d -> %d item per stare nei %d byte liberi"
                          % (before, len(self.items), self.max_growth))
        raise ZoneError("impossibile far stare il layout nello spazio libero")

    def _emit_text(self):
        self._fit_growth()
        blob = b"".join(item.new_bytes for item in self.items)
        expected = self.text_content_new_size
        if len(blob) != expected:
            raise ZoneError("byte emessi %d != attesi %d" % (len(blob), expected))
        blob += b"\x90" * self.text_pad_new
        if len(blob) != self.text_raw_size + self.raw_delta:
            raise ZoneError("dimensione .text incoerente: %d != %d"
                            % (len(blob), self.text_raw_size + self.raw_delta))
        return blob

    def _build_image(self, text_blob):
        new_image = bytearray(self.data[:self.text_raw_off])
        new_image += text_blob
        new_image += self.data[self.text_raw_off + self.text_raw_size:]
        return new_image

    def new_off(self, new_rva):
        """RVA dell'immagine nuova -> offset di file."""
        if self.text_va <= new_rva < self.text_va + self.text_raw_size + self.raw_delta:
            return self.text_raw_off + (new_rva - self.text_va)
        off = self.rva_to_off(new_rva - self.delta)
        if off is None:
            return None
        # la coda del file e' stata traslata dall'inserimento nella .text
        return off + self.raw_delta

    # -- patching ---------------------------------------------------------
    def _write_value(self, image, new_rva, width, value):
        off = self.new_off(new_rva)
        if off is None or off + width > len(image):
            raise ZoneError("patch fuori immagine a %#x" % new_rva)
        if width == 4:
            struct.pack_into("<I", image, off, value & 0xFFFFFFFF)
        elif width == 8:
            struct.pack_into("<Q", image, off, value & 0xFFFFFFFFFFFFFFFF)
        elif width == 2:
            struct.pack_into("<H", image, off, value & 0xFFFF)

    def _patch_headers(self, image):
        optional = self.pe.OPTIONAL_HEADER
        header = optional.dump_dict()
        delta = self.delta

        def field_off(name):
            return header[name]["FileOffset"]

        # dimensioni: la .text cresce sempre, la SizeOfImage solo se le
        # sezioni successive slittano (modalita' shift)
        if self.inserted_total:
            size_of_code = header["SizeOfCode"]["Value"] + self.raw_delta
            struct.pack_into("<I", image, field_off("SizeOfCode"), size_of_code)
        if delta:
            size_of_image = header["SizeOfImage"]["Value"] + delta
            struct.pack_into("<I", image, field_off("SizeOfImage"), size_of_image)

        # entry point: e' una RVA nel codice, va mappata
        entry = optional.AddressOfEntryPoint
        new_entry = self.map_point(entry)
        struct.pack_into("<I", image, field_off("AddressOfEntryPoint"), new_entry)

        # data directory: solo quelle che puntano a .text cambiano
        for index, directory in enumerate(optional.DATA_DIRECTORY):
            if not directory.VirtualAddress:
                continue
            if not (self.text_va <= directory.VirtualAddress < self.text_end_old):
                if not delta:
                    continue
                new_value = directory.VirtualAddress + delta
            else:
                new_value = self.map_point(directory.VirtualAddress)
            site = self._data_directory_site(index)
            struct.pack_into("<I", image, site, new_value)

        # sezioni: la .text cresce, le successive slittano (solo in shift)
        for section in self.sections:
            dumped = section.dump_dict()
            if section is self.text:
                vsize = section._zone_vs + self.inserted_total
                rawsize = section._zone_raw + self.raw_delta
                struct.pack_into("<I", image, dumped["Misc_VirtualSize"]["FileOffset"], vsize)
                struct.pack_into("<I", image, dumped["SizeOfRawData"]["FileOffset"], rawsize)
            elif section._zone_va > self.text_va:
                if delta:
                    va = section._zone_va + delta
                    struct.pack_into("<I", image, dumped["VirtualAddress"]["FileOffset"], va)
                if self.raw_delta:
                    pr = section._zone_pr + self.raw_delta
                    struct.pack_into("<I", image, dumped["PointerToRawData"]["FileOffset"], pr)

    def _apply_patches(self, image):
        applied = 0
        for site, width, mode, target, constant in self.patches:
            if site is None:
                continue
            new_site = self.map_point(site)
            if mode in ("rva", "rva-boundary", "rva-unwind"):
                if target is None:
                    continue
                value = self.repair_target(target)
            elif mode == "func-end":
                value = self.function_end.get(constant)
                if value is None:
                    value = self.repair_target(target)
            elif mode == "rva64":
                value = self.repair_target(target)
            elif mode == "rva-plain":
                value = self.map_point(target) if (
                    target is not None and self.in_image_rva(target)) else target
            elif mode == "va":
                value = self.image_base + self.repair_target(target)
            elif mode == "fileoff":
                value = constant + self.raw_delta
            else:
                continue
            self._write_value(image, new_site, width, value)
            applied += 1
        return applied

    def _patch_jump_tables(self, image):
        applied = 0
        for entry_rva, (mode, target_old) in getattr(self, "jumptable_entries", {}).items():
            new_site = self.map_point(entry_rva)
            new_target = self.map_point(target_old)
            if mode == "abs":
                value = new_target
            elif mode == "rel-entry":
                value = new_target - new_site
            elif mode == "rel-base":
                value = new_target - new_site  # base e entry coincidono
            else:
                continue
            self._write_value(image, new_site, 4, value & 0xFFFFFFFF)
            applied += 1
        return applied

    # -- API pubblica / compatibilita' ------------------------------------
    def create_label_table(self):
        """Nella v2 il disassembly avviene nel costruttore."""
        return len(self.branch_refs)

    def create_jmp_table(self):
        return len(self.jump_tables)

    def update_label_table(self):
        return 0

    def adjust_out_text_references(self):
        return 0

    def adjust_reloc_table(self):
        return 0

    def adjust_jmp_table(self):
        return 0

    def print_instructions(self):
        return None

    def print_blocks(self):
        return None

    def _range_blocked(self, ranges, start, end):
        for lo, hi in ranges:
            if start < hi and end > lo:
                return True
        return False

    def _can_touch(self, item):
        """True se l'istruzione puo' essere modificata in sicurezza."""
        if item.kind != "insn":
            return False
        if item.is_branch or item.rip_target is not None or item.abs_target is not None:
            return False
        return not self._range_blocked(self.no_resize_ranges, item.old_rva,
                                       item.old_rva + item.orig_size)

    def _can_insert_after(self, item):
        if item.kind != "insn":
            return False
        if item.cs_insn.id in self.TERMINATORS:
            return False
        if X86_GRP_RET in item.cs_insn.groups:
            return False
        if item.cs_insn.id == X86_INS_JMP:
            return False
        return not self._range_blocked(self.no_insert_ranges, item.old_rva,
                                       item.old_rva + item.orig_size)

    def _insert_after(self, index, items):
        for offset, new_item in enumerate(items):
            self.items.insert(index + 1 + offset, new_item)

    def _insert_before(self, index, items):
        for offset, new_item in enumerate(items):
            self.items.insert(index + offset, new_item)

    # -- suddivisione in blocchi -----------------------------------------
    def _is_block_terminator(self, item):
        if item.kind != "insn":
            # i trampolini di -ebi e i connettori di -ibp sono branch creati
            # da noi: chiudono comunque il blocco
            return bool(item.is_branch and item.is_uncond)
        insn = item.cs_insn
        if insn.id in self.TERMINATORS:
            return True
        if insn.id == X86_INS_JMP:
            return True
        if X86_GRP_RET in insn.groups or X86_GRP_IRET in insn.groups:
            return True
        # i salti condizionali chiudono il blocco (il fallthrough e' a parte)
        return X86_GRP_JUMP in insn.groups

    def _block_ends_unconditionally(self, block):
        """True se il blocco non ha fallthrough (jmp/ret/int3/...)."""
        last = block[-1]
        if last.kind != "insn":
            return bool(last.is_branch and last.is_uncond)
        insn = last.cs_insn
        if insn.id in self.TERMINATORS or insn.id == X86_INS_JMP:
            return True
        if X86_GRP_RET in insn.groups or X86_GRP_IRET in insn.groups:
            return True
        # un salto condizionale ha fallthrough: serve il connettore
        return False

    def _block_eligible(self, block):
        """Un blocco si puo' spostare solo se non tocca zone protette."""
        for item in block:
            if item.kind == "seq" and item.role == "tramp":
                continue                      # trampolino creato da -ebi
            if item.kind != "insn" or item.old_rva is None:
                return False
            if item.role in ("connector", "bcf"):
                return False
            if self._range_blocked(self.no_resize_ranges, item.old_rva,
                                   item.old_rva + item.orig_size):
                return False
        return True

    def _split_blocks(self):
        """Divide gli item in unita' di layout.

        Ritorna una lista di unita' nell'ordine di emissione:
            ("data", None, item)        un blocco dati (mai permutato)
            ("block", chiave, [item])   un blocco di codice, con la chiave
                                        della funzione di appartenenza

        Solo i blocchi con la stessa chiave e consecutivi si possono
        permutare fra loro: cosi' il range `.pdata` di una funzione resta
        contiguo e i range delle altre funzioni non vengono invasi.
        """
        functions = sorted(self.runtime_functions, key=lambda f: f["begin"])
        begins = [f["begin"] for f in functions]

        def group_of(rva):
            position = bisect.bisect_right(begins, rva) - 1
            if position < 0:
                return None
            function = functions[position]
            if function["begin"] <= rva < function["end"]:
                return function["begin"]
            return None

        units = []
        block = []
        position = 0
        while position < len(self.items):
            item = self.items[position]
            position += 1
            if item.kind == "data":
                if block:
                    units.append(("block", group_of(block[0].old_rva), block))
                    block = []
                units.append(("data", None, item))
                continue
            key = group_of(item.old_rva) if item.old_rva is not None else None
            if block and group_of(block[0].old_rva) != key:
                units.append(("block", group_of(block[0].old_rva), block))
                block = []
            block.append(item)
            if not self._is_block_terminator(item):
                continue
            # i trampolini di -ebi sono atomici: il salto locale del `loop`
            # conta sulla contiguita' fisica dei due jmp che seguono
            if (item.role == "tramp" and position < len(self.items)
                    and self.items[position].role == "tramp"):
                continue
            units.append(("block", key, block))
            block = []
        if block:
            units.append(("block", group_of(block[0].old_rva), block))
        return units

    def _new_jmp_item(self, target_old=None, role="connector", target_item=None):
        """Un `jmp rel32` nuovo, con target in RVA vecchia o come item."""
        item = Instruction("seq", None, 5, b"\xe9\x00\x00\x00\x00")
        item.is_branch = True
        item.is_uncond = True
        item.imm_off = 1
        item.imm_size = 4
        item.opcode = 0xE9
        item.target_old = target_old
        item.target_item = target_item
        item.role = role
        return item

    def _new_seq(self, raw, role, label=None):
        item = Instruction("seq", None, len(raw), bytes(raw))
        item.new_bytes = bytes(raw)
        item.role = role
        item.label = label
        return item

    def _budget_left(self):
        if self.growth_mode != "slack":
            return None
        used = 0
        for item in self.items:
            if item.old_rva is None:
                used += item.size
        # margine per l'allargamento dei branch rel8 -> rel32
        return max(0, self.max_growth - 256 - used)

    def _require_coverage(self, what, force):
        """Tutti i passi che spostano byte richiedono copertura completa.

        Se nella .text resta codice non riconosciuto, spostarlo significa
        lasciare sbagliati i suoi riferimenti RIP-relative: meglio fermarsi.
        """
        ratio, blocks, size = self.coverage()
        self.info("copertura della .text: %.2f%% (%d blocchi sospetti, %d byte)"
                  % (ratio * 100, blocks, size))
        if blocks and not force:
            raise ZoneError(
                "la .text contiene %d blocchi (%d byte) che non sono ne' codice "
                "riconosciuto ne' padding: %s sposterebbe quel codice senza "
                "poter correggere i suoi riferimenti.\n"
                "Usa --eq (sostituzioni a dimensione costante, sicure) oppure "
                "--force se sai che quei byte sono davvero dati."
                % (blocks, size, what))

    # -- pass: -ebi, espansione dei branch corti jrcxz/loop --------------
    def eliminate_bad_instructions(self, force=False):
        """Espande jrcxz/loop in un trampolino a due salti.

        Originale:      `loop target`                     (2 byte, rel8)
        Diventa:
            A+0:  loop A+7              ; "preso" -> salta il jmp del fallthrough
            A+2:  jmp fallthrough       ; "non preso" -> percorso originale
            A+7:  jmp target            ; percorso "preso"
            A+12: fallthrough

        Il `loop` usa solo un rel8 locale, quindi non puo' piu' finire fuori
        range quando le inserzioni successive spostano il codice.
        """
        self._require_coverage("--ebi", force)
        expanded = 0
        index = 0
        while index < len(self.items):
            item = self.items[index]
            index += 1
            if item.kind != "insn" or item.old_rva is None:
                continue
            if item.target_old is None or not item.is_branch:
                continue
            raw = item.orig_bytes
            if len(raw) < 2 or item.imm_size != 1:
                continue
            opcode_index = item.imm_off - 1
            opcode = raw[opcode_index] if opcode_index >= 0 else None
            if opcode not in (0xE0, 0xE1, 0xE2, 0xE3):
                continue
            if self._range_blocked(self.no_resize_ranges, item.old_rva,
                                   item.old_rva + item.orig_size):
                continue
            budget = self._budget_left()
            if budget is not None and budget < 10:
                break
            # indirizzo del fallthrough originale
            if index < len(self.items) and self.items[index].old_rva is not None:
                fallthrough_old = self.items[index].old_rva
            else:
                fallthrough_old = self.text_end_old
            prefix = raw[:opcode_index]
            local = self._new_seq(prefix + bytes([opcode, 0x05]), "tramp",
                                  "ebi-local")
            # il trampolino eredita l'indirizzo dell'istruzione originale:
            # chi saltava qui deve continuare a saltare qui
            local.old_rva = item.old_rva
            jump_fallthrough = self._new_jmp_item(fallthrough_old, role="tramp")
            jump_target = self._new_jmp_item(item.target_old, role="tramp")
            self.items[index - 1:index] = [local, jump_fallthrough, jump_target]
            index += 2
            expanded += 1
        self.info("eliminate_bad_instructions: %d loop/jrcxz espansi" % expanded)
        return expanded

    # -- pass: -ibp, permutazione dei blocchi ----------------------------
    def block_permutation(self, probability=100, force=False):
        """Divide in blocchi, aggiunge i `jmp` di concatenamento e li mischia.

        Il primo blocco di ogni funzione resta primo: i codici di unwind di
        `.pdata` descrivono il prologo come offset dall'inizio funzione.
        Le funzioni con exception handler non vengono toccate.
        """
        self._require_coverage("--ibp", force)
        units = self._split_blocks()
        rebuilt = []
        permuted_groups = 0
        permuted_blocks = 0
        budget = self._budget_left()
        index = 0
        while index < len(units):
            kind, key, payload = units[index]
            if kind == "data":
                rebuilt.append(payload)
                index += 1
                continue
            # run di blocchi consecutivi della stessa funzione
            end = index
            while (end < len(units) and units[end][0] == "block"
                   and units[end][1] == key):
                end += 1
            blocks = [units[position][2] for position in range(index, end)]
            index = end
            if (len(blocks) >= 3
                    and self.rng.randint(0, 100) <= probability
                    and all(self._block_eligible(block) for block in blocks)):
                need = sum(1 for block in blocks[:-1]
                           if not self._block_ends_unconditionally(block)) * 5
                if budget is not None and need > budget:
                    rebuilt.extend(item for block in blocks for item in block)
                    continue
                # connettore esplicito: serve a ogni blocco che ha un
                # fallthrough, compresi quelli che finiscono con un jcc
                for position, block in enumerate(blocks[:-1]):
                    if self._block_ends_unconditionally(block):
                        continue
                    next_block = blocks[position + 1]
                    block.append(self._new_jmp_item(
                        target_item=next_block[0]))
                # primo e ultimo blocco restano al loro posto: il primo per i
                # codici di unwind, l'ultimo perche' il suo fallthrough esce
                # dal gruppo e non va spostato
                first, last = blocks[0], blocks[-1]
                middle = blocks[1:-1]
                self.rng.shuffle(middle)
                for block in [first] + middle + [last]:
                    rebuilt.extend(block)
                permuted_groups += 1
                permuted_blocks += len(blocks)
                if budget is not None:
                    budget -= need
            else:
                rebuilt.extend(item for block in blocks for item in block)
        self.items = rebuilt
        if permuted_groups:
            self.permuted = True
        self.info("block_permutation: %d funzioni, %d blocchi permutati"
                  % (permuted_groups, permuted_blocks))
        return permuted_groups

    # -- pass: -bcf, bogus control flow ----------------------------------
    # Predicati opachi *provabili*: usano il valore di rsp (che dipende da
    # ASLR e dallo stack) ma la condizione e' sempre vera per costruzione,
    # quindi non serve conoscerlo all'atto della trasformazione.
    #   1) (rsp & 0xf) < 0x10                  sempre vero
    #   2) (rsp | 1) & 1 != 0                  sempre vero
    #   3) ((rsp >> 3) & 0x7) < 8              sempre vero
    #   4) rsp - rsp == 0                      sempre vero
    OPAQUE_PREDICATES = (
        ("r11", b"\x49\x89\xe3"                  # mov r11, rsp
               b"\x49\x83\xe3\x0f"               # and r11, 0xf
               b"\x49\x83\xfb\x10"               # cmp r11, 0x10
               b"\x72", 0x72),                   # jb rel8
        ("r11", b"\x49\x89\xe3"                  # mov r11, rsp
               b"\x49\x83\xcb\x01"               # or r11, 1
               b"\x41\xf6\xc3\x01"               # test r11b, 1
               b"\x75", 0x75),                   # jnz rel8
        ("r11", b"\x49\x89\xe3"                  # mov r11, rsp
               b"\x49\xc1\xeb\x03"               # shr r11, 3
               b"\x49\x83\xe3\x07"               # and r11, 7
               b"\x49\x83\xfb\x08"               # cmp r11, 8
               b"\x72", 0x72),                   # jb rel8
        ("r11", b"\x49\x89\xe3"                  # mov r11, rsp
               b"\x49\x29\xe3"                   # sub r11, rsp
               b"\x4d\x85\xdb"                   # test r11, r11
               b"\x74", 0x74),                   # jz rel8
    )

    def _bcf_sequence(self):
        """pushfq; push r11; <predicato>; jcc oltre_il_finto; <finto>;
        pop r11; popfq

        Il `jcc` scavalca solo il blocco finto, che e' innocuo: anche se il
        predicato fosse valutato male, l'esecuzione attraversa il finto e
        arriva comunque ai `pop`, quindi la semantica resta corretta.
        """
        register, predicate, jcc_opcode = self.rng.choice(self.OPAQUE_PREDICATES)
        junk = bytes(self._nop_sequence()) or b"\x90"
        while len(junk) > 120:                    # il disp del jcc e' rel8
            junk = junk[:len(junk) // 2]
        jump_offset = len(predicate) - 1          # ultimo byte = opcode del jcc
        code = bytearray(predicate)
        code.append(len(junk))                    # displacement rel8 del jcc
        blob = bytearray()
        blob += b"\x9c"                           # pushfq
        blob += b"\x41\x53"                       # push r11
        blob += code
        blob += junk
        blob += b"\x41\x5b"                       # pop r11
        blob += b"\x9d"                           # popfq
        return bytes(blob)

    def bogus_control_flow(self, probability=15, force=False):
        """Inserisce un predicato opaco con un blocco finto non raggiunto.

        Sequenza inserita *prima* dell'istruzione scelta:

            pushfq
            push r11
            <predicato sempre vero>
            jcc  dopo_il_finto
            <blocco finto: istruzioni innocue + jmp dopo_il_finto>
        dopo_il_finto:
            pop r11
            popfq
            <istruzione originale>

        Flag e r11 vengono ripristinati, lo stack resta bilanciato.
        """
        self._require_coverage("--bcf", force)
        inserted = 0
        index = 0
        while index < len(self.items):
            item = self.items[index]
            index += 1
            if item.kind != "insn" or item.old_rva is None:
                continue
            if self.rng.randint(0, 100) > probability:
                continue
            if not self._can_insert_after(item) and not self._can_touch(item):
                continue
            if self._range_blocked(self.no_insert_ranges, item.old_rva,
                                   item.old_rva + item.orig_size):
                continue
            blob = self._bcf_sequence()
            budget = self._budget_left()
            if budget is not None and len(blob) > budget:
                break
            chunk = self._new_seq(blob, "bcf", "bcf")
            self._insert_before(index - 1, [chunk])
            index += 1
            inserted += 1
        self.info("bogus_control_flow: %d predicati opachi inseriti" % inserted)
        return inserted

    # -- pass: sostituzioni equivalenti ----------------------------------
    def equal_instructions(self, probability=100):
        """Sostituzioni *provatamente* equivalenti sui flag.

        La v1 riscriveva xor reg,reg con mov reg,0 (i flag cambiano!),
        inc con add (cambia CF) e push reg con mov rax/ push rax (clobbera
        rax). Qui restano solo le identita' che preservano risultato e flag.
        """
        changed = 0
        for item in list(self.items):
            if self.rng.randint(0, 100) > probability:
                continue
            if not self._can_touch(item):
                continue
            insn = item.cs_insn
            mnemonic = insn.mnemonic
            operands = insn.operands
            text = None
            if mnemonic in ("add", "sub") and len(operands) == 2:
                if operands[0].type == X86_OP_REG and operands[1].type == X86_OP_IMM:
                    value = operands[1].imm
                    if -(2 ** 31) <= -value < 2 ** 31:
                        other = "sub" if mnemonic == "add" else "add"
                        text = "%s %s,%d" % (other, insn.reg_name(operands[0].reg),
                                             -value)
            elif mnemonic == "xor" and len(operands) == 2:
                if (operands[0].type == X86_OP_REG
                        and operands[1].type == X86_OP_REG
                        and operands[0].reg == operands[1].reg):
                    text = "sub %s,%s" % (insn.reg_name(operands[0].reg),
                                          insn.reg_name(operands[1].reg))
            elif mnemonic == "test" and len(operands) == 2:
                if (operands[0].type == X86_OP_REG and operands[1].type == X86_OP_REG
                        and operands[0].reg == operands[1].reg):
                    text = "cmp %s,0" % insn.reg_name(operands[0].reg)
            if text is None:
                continue
            try:
                encoded, _ = self.ks.asm(text, item.old_rva)
            except Exception:
                continue
            encoded = bytes(encoded)
            if not encoded:
                continue
            # in modalita' slack la sostituzione non deve far crescere la
            # sezione: le forme piu' lunghe vengono scartate
            if self.growth_mode == "slack" and len(encoded) > item.orig_size:
                continue
            item.replacement = encoded
            item.label = text
            changed += 1
        self.info("equal_instructions: %d sostituzioni" % changed)
        return changed

    # -- pass: nop casuali ------------------------------------------------
    def _nop_sequence(self):
        register = self.rng.choice(
            ["rax", "rbx", "rcx", "rdx", "rsi", "rdi", "r8", "r9", "r10",
             "r11", "r12", "r13", "r14", "r15"])
        choice = self.rng.choice(["nop", "sub", "add", "mov", "lea", "or",
                                  "xor", "and", "sar", "shr", "shl", "jmp"])
        try:
            if choice == "nop":
                text = "pushfq;nop;nop;popfq"
            elif choice in ("sub", "add", "xor", "sar", "shr", "shl", "rcl", "rcr"):
                text = "pushfq;%s %s,0x0;popfq" % (choice, register)
            elif choice == "mov":
                text = "pushfq;mov %s,%s;popfq" % (register, register)
            elif choice == "lea":
                text = "pushfq;lea %s,[%s+0];popfq" % (register, register)
            elif choice == "or":
                text = "pushfq;or %s,%s;popfq" % (register, register)
            elif choice == "and":
                text = "pushfq;and %s,%s;popfq" % (register, register)
            elif choice == "jmp":
                return bytearray(b"\x9c") + bytearray([0xEB, 0x00]) + bytearray(b"\x9d")
            else:
                return bytearray(b"\x9c\x90\x9d")
            encoded, _ = self.ks.asm(text, 0)
        except Exception:
            return bytearray(b"\x9c\x90\x9d")
        if not encoded:
            return bytearray(b"\x9c\x90\x9d")
        return bytearray(encoded)

    def coverage(self):
        """Quanto codice e' stato identificato dentro la .text.

        Un blocco dati conta come "sospetto" solo se e' **raggiungibile**:
        se nessuna reference (branch, RIP, tabella, relocation, `.pdata`,
        puntatore nei dati) cade dentro di lui e nessuna istruzione ci
        arriva in fallthrough, allora e' codice morto o dati e spostarlo
        non rompe nulla.  Il padding (anche multi-byte) e le jump table
        gia' riconosciute non contano.
        """
        targets = set()
        for item in self.items:
            if item.is_branch and item.target_old is not None:
                targets.add(item.target_old)
            if item.rip_target is not None:
                targets.add(item.rip_target)
            if item.abs_target is not None:
                targets.add(item.abs_target)
        targets.update(getattr(self, "jumptable_entries", {}))
        for site, width, mode, target, constant in self.patches:
            if target is not None and mode in ("rva", "rva-boundary",
                                               "rva-unwind", "rva64", "va"):
                targets.add(target)
        for function in self.runtime_functions:
            targets.add(function["begin"])
        targets.add(self.pe.OPTIONAL_HEADER.AddressOfEntryPoint)
        sorted_targets = sorted(targets)

        data_bytes = 0
        data_blocks = 0
        for index, item in enumerate(self.items):
            if item.kind != "data" or item.old_rva is None:
                continue
            if item.old_rva >= self.text_rva_end_vsize:
                continue                       # coda raw, non mappata
            if self._is_padding_block(item):
                continue
            if item.role == "table":
                continue                       # tabella gia' riconosciuta
            if any(lo <= item.old_rva < hi for lo, hi in self.jumptable_ranges):
                continue                       # tabella gia' riconosciuta
            lo, hi = item.old_rva, item.old_rva + item.size
            position = bisect.bisect_left(sorted_targets, lo)
            reachable = (position < len(sorted_targets)
                         and sorted_targets[position] < hi)
            if not reachable and index > 0:
                previous = self.items[index - 1]
                if previous.kind == "insn" and previous.old_rva is not None:
                    # fallthrough vero solo se il blocco inizia con
                    # un'istruzione decodificabile: altrimenti il blocco
                    # precedente si e' fermato su un errore di decodifica
                    reachable = (previous.old_rva + previous.orig_size == lo
                                 and not self._block_ends_unconditionally([previous])
                                 and self._decode_one(lo) is not None)
            if reachable:
                data_blocks += 1
                data_bytes += item.size
        total = max(1, self.text_vsize)
        return 1.0 - data_bytes / total, data_blocks, data_bytes

    def _is_padding_block(self, item):
        """True se il blocco e' padding (int3/zeri o solo NOP, anche lunghi)."""
        data = item.data
        if not data:
            return True
        if data[0] in (0xCC, 0x00):
            return True
        total = 0
        for insn in self.cs.disasm(data, item.old_rva):
            if insn.mnemonic != "nop":
                return False
            total += insn.size
        return total == len(data)

    def insert_random_nop(self, probability=10, force=False):
        """Inserisce sequenze che non cambiano ne' registri ne' flag."""
        ratio, blocks, size = self.coverage()
        self.info("copertura della .text: %.2f%% (%d blocchi dati sospetti, %d byte)"
                  % (ratio * 100, blocks, size))
        if blocks and not force:
            raise ZoneError(
                "la .text contiene %d blocchi (%d byte) che non sono ne' codice "
                "riconosciuto ne' padding: inserire istruzioni sposterebbe quel "
                "codice senza poter correggere i suoi riferimenti.\n"
                "Usa --eq (sostituzioni a dimensione costante, sicure) oppure "
                "--force se sai che quei byte sono davvero dati."
                % (blocks, size))
        inserted = 0
        added = 0
        budget = self.max_growth if self.growth_mode == "slack" else None
        if budget is not None:
            budget = max(0, budget - 64)   # margine per l'allargamento dei branch
        index = 0
        while index < len(self.items):
            item = self.items[index]
            index += 1
            if self.rng.randint(0, 100) > probability:
                continue
            if not self._can_insert_after(item):
                continue
            blob = self._nop_sequence()
            if not blob:
                continue
            count = self.rng.randint(1, 2)
            if budget is not None:
                if added + len(blob) * count > budget:
                    # spazio finito: ci si ferma (nessun troncamento a valle)
                    self.info("insert_random_nop: budget di %d byte esaurito"
                              % budget)
                    break
            new_items = []
            for _ in range(count):
                chunk = Instruction("seq", None, len(blob), bytes(blob))
                chunk.new_bytes = bytes(blob)
                chunk.role = "nop"
                new_items.append(chunk)
            self._insert_after(index - 1, new_items)
            index += len(new_items)
            inserted += len(new_items)
            added += len(blob) * count
        self.added_bytes = added
        self.info("insert_random_nop: %d sequenze inserite (%d byte)"
                  % (inserted, added))
        return inserted

    # -- scrittura --------------------------------------------------------
    def write_pe_file(self, output=None, output_path=None, allow_in_place=False):
        """Scrive l'immagine riscritta in un file (mai sull'input).

        Il file di input resta aperto da pefile: scriverci sopra e' la via
        piu' rapida per un errore di condivisione, quindi l'output e' sempre
        un file nuovo (default `<nome>_zone<ext>`).  `allow_in_place=True`
        (dalla CLI: `--in-place`) abilita la sovrascrittura esplicita.
        """
        if output is None:
            output = output_path or self.default_output_path()
        if (not allow_in_place
                and os.path.abspath(output) == os.path.abspath(self.file)):
            raise ZoneError(
                "l'output non puo' essere il file di input (%s): usa -o per "
                "scegliere un nome diverso, oppure --in-place se proprio "
                "vuoi sovrascriverlo" % output)
        text_blob = self._emit_text()
        image = self._build_image(text_blob)
        self._patch_headers(image)
        applied = self._apply_patches(image)
        tables = self._patch_jump_tables(image)
        self.info("patch applicate: %d dati + %d jump table entry (delta %#x)"
                  % (applied, tables, self.delta))
        if self.check_hook:
            self.check_hook(image)
        # chiude l'handle di pefile sull'input prima di scrivere
        try:
            self.pe.close()
        except Exception:
            pass
        try:
            with open(output, "wb") as handle:
                handle.write(image)
        except OSError as error:
            raise ZoneError(
                "non riesco a scrivere %s (%s). Se il file e' in esecuzione o "
                "e' aperto da un altro programma, chiudilo oppure usa -o con un "
                "altro nome." % (output, error))
        self.info("scritto %s (%d byte)" % (output, len(image)))
        return output

    def default_output_path(self):
        """`payload.exe` -> `payload_zone.exe` (senza sovrascrivere nulla)."""
        base, extension = os.path.splitext(self.file)
        candidate = base + "_zone" + extension
        counter = 2
        while os.path.exists(candidate):
            candidate = "%s_zone%d%s" % (base, counter, extension)
            counter += 1
        return candidate

    # -- verifica ---------------------------------------------------------
    def verify(self, path):
        """Ricontrolla il file scritto: reference, .pdata, entry point."""
        with open(path, "rb") as handle:
            data = handle.read()
        pe = pefile.PE(data=data)

        def read_at(rva, size):
            for section in pe.sections:
                if section.VirtualAddress <= rva < section.VirtualAddress + max(
                        section.Misc_VirtualSize, section.SizeOfRawData):
                    off = section.PointerToRawData + (rva - section.VirtualAddress)
                    return data[off:off + size], off
            return None, None

        errors = []
        checked = 0

        def check_branch(item):
            nonlocal checked
            new_site = item.new_rva
            raw, _ = read_at(new_site, 16)
            if raw is None:
                errors.append("branch %#x->%#x: sito non leggibile"
                              % (item.old_rva or 0, new_site))
                return
            found = None
            for insn in self.cs.disasm(raw, new_site, 1):
                found = insn
                break
            if found is None:
                errors.append("branch %#x: non decodificabile" % new_site)
                return
            if not found.groups or (X86_GRP_JUMP not in found.groups
                                    and X86_GRP_CALL not in found.groups
                                    and X86_GRP_BRANCH_RELATIVE not in found.groups):
                errors.append("branch %#x: non e' piu' un branch (%s)"
                              % (new_site, found.mnemonic))
                return
            if not found.operands or found.operands[0].type != X86_OP_IMM:
                errors.append("branch %#x: target non immediato" % new_site)
                return
            expected = (item.target_item.new_rva if item.target_item is not None
                        else self.map_point(item.target_old))
            if found.operands[0].imm != expected:
                errors.append("branch %#x: target %#x != atteso %#x"
                              % (new_site, found.operands[0].imm, expected))
            checked += 1

        # verifica ogni item-branch: copre anche i trampolini di -ebi e i
        # connettori di -ibp, che non stanno in branch_refs
        for item in self.items:
            if not item.is_branch:
                continue
            if item.target_item is not None:
                check_branch(item)
                continue
            if item.target_old is None:
                continue
            if not (self.text_va <= item.target_old < self.text_end_old):
                continue
            check_branch(item)

        for item in self.items:
            if item.kind != "insn" or item.rip_target is None:
                continue
            new_site = item.new_rva
            raw, _ = read_at(new_site, item.size)
            if raw is None:
                continue
            for insn in self.cs.disasm(raw, new_site, 1):
                disp = None
                for operand in insn.operands:
                    if operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP:
                        disp = operand.mem.disp
                if disp is None:
                    continue
                target = new_site + insn.size + disp
                expected = self.map_point(item.rip_target)
                if target != expected:
                    errors.append("rip %#x: target %#x != atteso %#x"
                                  % (new_site, target, expected))
                checked += 1
            break

        # .pdata: ogni begin deve decodificare, end > begin, unwind leggibile
        directory = pe.OPTIONAL_HEADER.DATA_DIRECTORY[3]
        pdata_errors = 0
        for index in range(directory.Size // 12):
            raw, _ = read_at(directory.VirtualAddress + index * 12, 12)
            if raw is None or len(raw) < 12:
                break
            begin, end, unwind = struct.unpack("<III", raw)
            if not (pe.sections[0].VirtualAddress <= begin < pe.OPTIONAL_HEADER.SizeOfImage):
                pdata_errors += 1
                continue
            if end <= begin:
                pdata_errors += 1
            info_raw, _ = read_at(unwind & ~1, 4)
            if info_raw is None or len(info_raw) < 4:
                pdata_errors += 1
        if pdata_errors:
            errors.append(".pdata: %d/%d entry incoerenti"
                          % (pdata_errors, directory.Size // 12))

        # entry point
        entry = pe.OPTIONAL_HEADER.AddressOfEntryPoint
        raw, _ = read_at(entry, 16)
        decoded = None
        if raw:
            for insn in self.cs.disasm(raw, entry, 1):
                decoded = insn
                break
        if decoded is None:
            errors.append("entry point %#x non decodificabile" % entry)

        return checked, errors

    check_hook = None


# ---------------------------------------------------------------------------
# self test: round trip senza modifiche
# ---------------------------------------------------------------------------

def _roundtrip(path, verbose=False):
    zone = Zone(path, verbose=verbose)
    zone._layout()
    blob = b"".join(item.new_bytes for item in zone.items)
    original = bytes(zone.data[zone.text_raw_off:zone.text_raw_off + zone.text_raw_size])
    return blob == original, zone


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Zone PE v2 - bin2bin rewriter per x64 PE")
    parser.add_argument("file")
    parser.add_argument("-o", "--output", default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--eq", dest="eq", action="store_true", default=True,
                        help="sostituzioni equivalenti (default on)")
    parser.add_argument("--no-eq", dest="eq", action="store_false")
    parser.add_argument("--nop", dest="nop", action="store_true", default=False,
                        help="inserimento di nop (richiede copertura completa)")
    parser.add_argument("--no-nop", dest="nop", action="store_false")
    parser.add_argument("--force", action="store_true",
                        help="forza --nop anche se la .text non e' coperta al 100 per cento")
    parser.add_argument("--grow", choices=("slack", "shift"), default="slack",
                        help="slack: cresce solo nello spazio libero (sicuro); "
                             "shift: sposta le sezioni successive")
    parser.add_argument("--ebi", dest="ebi", action="store_true",
                        help="espande jrcxz/loop in trampolini espliciti")
    parser.add_argument("--ibp", dest="ibp", action="store_true",
                        help="permutazione dei blocchi (con jmp di concatenamento)")
    parser.add_argument("--bcf", dest="bcf", action="store_true",
                        help="bogus control flow: predicati opachi + blocco finto")
    parser.add_argument("--nop-probability", type=int, default=10)
    parser.add_argument("--ibp-probability", type=int, default=100)
    parser.add_argument("--bcf-probability", type=int, default=15)
    parser.add_argument("--check", action="store_true",
                        help="verifica le reference del file prodotto")
    parser.add_argument("--in-place", dest="in_place", action="store_true",
                        help="sovrascrive il file di input (default: scrive "
                             "<nome>_zone<ext>)")
    parser.add_argument("--roundtrip", action="store_true",
                        help="self test: il layout senza pass deve essere identico")
    parser.add_argument("--log", default=None)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    log = open(args.log, "w") if args.log else None
    try:
        if args.roundtrip:
            ok, _ = _roundtrip(args.file, verbose=not args.quiet)
            print("roundtrip: %s" % ("OK" if ok else "DIVERSO"))
            return 0 if ok else 1

        zone = Zone(args.file, seed=args.seed, verbose=not args.quiet, log=log,
                    growth=args.grow)
        zone.create_jmp_table()
        zone.create_label_table()
        # stesso ordine del pipeline di pobf.py: ebi, eq, ibp, bcf, nop
        if args.ebi:
            zone.eliminate_bad_instructions(force=args.force)
        if args.eq:
            zone.equal_instructions()
        if args.ibp:
            zone.block_permutation(probability=args.ibp_probability,
                                   force=args.force)
        if args.bcf:
            zone.bogus_control_flow(probability=args.bcf_probability,
                                    force=args.force)
        if args.nop:
            zone.insert_random_nop(probability=args.nop_probability,
                                   force=args.force)

        # l'output e' sempre un file nuovo: `-o` per sceglierlo, `--in-place`
        # per sovrascrivere l'input
        if args.in_place:
            output = args.output or args.file
        else:
            output = args.output or zone.default_output_path()

        if args.check:
            import tempfile
            handle, temp_name = tempfile.mkstemp(suffix=".exe")
            os.close(handle)
            zone.write_pe_file(temp_name)
            checked, errors = zone.verify(temp_name)
            print("verifica: %d reference controllate" % checked)
            for error in errors[:40]:
                print("  ERRORE:", error)
            if len(errors) > 40:
                print("  ... altri %d errori" % (len(errors) - 40))
            if errors:
                os.replace(temp_name, output)
                print("file comunque scritto in", output)
                return 1
            os.replace(temp_name, output)
            print("scritto", output)
            return 0
        zone.write_pe_file(output, allow_in_place=args.in_place)
        print("scritto", output)
        return 0
    except ZoneError as error:
        print("ERRORE:", error, file=sys.stderr)
        return 2
    finally:
        if log:
            log.close()


if __name__ == "__main__":
    sys.exit(main())
