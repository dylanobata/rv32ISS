#! /usr/bin/env python3

# single cycle datapath RISC-V 32I
# Stages of RISCV datapath:
    # fetch
    # decode
    # execute
    # Used by load/store instructions only:
    #     memory access
    #     register writeback

# import argparse
from bitstring import BitArray
from enum import Enum
import glob
from elftools.elf.elffile import ELFFile

class Opcode(Enum):
    LUI = BitArray(bin = '0b0110111') # load upper immediate
    AUIPC = BitArray(bin = '0b0010111') # Add upper immediate to PC 
    JAL = BitArray(bin= '0b1101111') # Jump and link 
    JALR = BitArray(bin = '0b1100111') # Jump and link register
    BRANCH = BitArray(bin = '0b1100011')
    LOAD = BitArray(bin = '0b0000011')
    STORE = BitArray(bin = '0b0100011')
    IMM =  BitArray(bin = '0b0010011') # Immediate instructions
    OP = BitArray(bin = '0b0110011') # Arithmetic/Logic Ops 
    MISCMEM = BitArray(bin = '0b0001111')
    SYS = BitArray(bin = '0b1110011') # System instructions


class Funct3(Enum):
    JALR = BEQ = LB = \
    SB = ADDI = ADD = SUB = \
    FENCE = ECALL = EBREAK = BitArray(bin = '0b000')
    
    BNE = LH = SH = \
    SLLI = SLL = FENCEI = CSRRW = BitArray(bin = '0b001')

    BLT = LBU = XORI = XOR = BitArray(bin = '0b100')

    BGE = LHU = SRLI = SRAI = \
    SRL = SRA = CSRRWI = BitArray(bin = '0b101')

    BLTU = ORI = OR = CSRRSI =  BitArray(bin = '0b110')

    BGEU = ANDI = AND = CSRRCI =  BitArray(bin = '0b111')
    
    LW = SW = SLTI = \
    SLT = CSRRS = BitArray(bin = '0b010')
    
    SLTIU = SLTU = CSRRC =  BitArray(bin = '0b011')


class Funct7(Enum):
    SRAI = SUB = SRA = BitArray(bin = '0b0100000')

    SLLI = SRLI = ADD = \
    SLL = SLT = SLTU = \
    XOR = SRL = OR = AND = BitArray(bin = '0b0000000')


class Regfile():
    def __init__(self):
        self.registers = [0] * 33 # x0-x31 and PC

    def __getitem__(self, key):
        return self.registers[key]
    
    def __setitem__(self, key, value):
        if key == 0: # x0 register is always 0
            return
        self.registers[key] = value & 0xFFFFFFFF


# GLOBAL VARIABLES
regfile = None
memory = None 
PC = 32 # PC is at index 32 in the regfile

def reset():
    global regfile, memory
    regfile = Regfile()
    # 16 MB memory, byte addressable, starting at 0x8000000
    memory = bytearray(0x1000000)


def loader(data, address):
    address -= 0x80000000 # subtract offset to get back to 0 index
    if address < 0 or address > len(memory):
        raise Exception("read out of bounds")
    memory[address:len(data)] = data


def fetch(address):
    address -= 0x80000000 
    return BitArray(uint = int.from_bytes(memory[address:address+4], byteorder = "little"), length = 32)


def decode(instruction):
    opcode = Opcode(instruction[25:]) # 7 bits
    print(instruction.hex, opcode)
#    if opcode == Opcode.ADDI.value:
#        rd = instruction[20:25] #  5 bits
#        funct3 = instruction[17:20] # 3 bits
#        rs1 = instruction[12:17] # 5 bits
#        immediate = instruction[0:12] # 12 bits 
#        print("rd: ", rd.bin)
#        print("funct3: ", funct3.bin)
#        print("rs1: ", rs1.bin)
#        print("immediate: ", immediate.bin)


def execute():
    pass


def memory_access():
    pass


def write_back():
    pass


def hart_dump():
    reg_names = ["x" + str(i) for i in range(32)] + ["PC"] 
    file = [] 
    for i in range(len(reg_names)):
        if i != 0 and i % 8 == 0:
            file += "\n"
        file += " %3s: %08x" % (reg_names[i], regfile[i])
    print(''.join(file))


def cycle() -> bool:
    # Fetch
    instruction = fetch(regfile[PC])
    print(instruction)

    # Decode
    decode(instruction) 
    regfile[PC] += 4 # get next word (4 bytes)

    # Execute
    hart_dump() 

    # Memory access

    # Write back
    return False


if __name__ == "__main__":
    for test_file in glob.glob("riscv-tests/isa/rv32ui-p-*"):
        if test_file.endswith('.dump'):
            continue
        with open(test_file, 'rb') as f:
            elf_file = ELFFile(f)
            print(test_file, ":\n")
            reset() # reset memory and PC for next program 
            regfile[PC] = 0x80000000  
            # ELF loader loads program into memory at location 0x80000000 
            for segment in elf_file.iter_segments(): 
                loader(segment.data(), segment.header.p_paddr) 
           #     print(memory[:len(segment.data())]) 
            instruction_count = 0
            while cycle():
                instruction_count += 1
 
            exit(0)
