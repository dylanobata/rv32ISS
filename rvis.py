#!usr/bin/env python3

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
import opcode as op


class Regfile():
    def __init__(self):
        self.registers = [0] * 33 # x0-x31 and PC
    
    def __getitem__(self, key):
        return self.registers[key]
    
    def __setitem__(self, key, value):
        if key == 0: # x0 register is always 0
            return
        self.registers[key] = value & 0xFFFFFFFF

regfile = None
memory = None 
PC = 32 # PC is at index 32 in the regfile

def reset():
    global regfile, memory
    regfile = Regfile()
    # 16 MB memory, byte addressable
    memory = bytearray(0x1000000)

def fetch():
    if regfile[PC] < 0 or regfile[PC] > len(memory):
        raise Exception("read out of bounds")
    return BitArray(uint = int.from_bytes(memory[regfile[PC]:regfile[PC]+4], byteorder = "big"), length = 32)


def decode(instruction):
    opcode = instruction[25:] # 7 bits
    if opcode == op.Opcode.ADDI.value:
        rd = instruction[20:25] #  5 bits
        funct3 = instruction[17:20] # 3 bits
        rs1 = instruction[12:17] # 5 bits
        immediate = instruction[0:12] # 12 bits 
        print("rd: ", rd.bin)
        print("funct3: ", funct3.bin)
        print("rs1: ", rs1.bin)
        print("immediate: ", immediate.bin)
    print("opcode: ", opcode.bin)
    print(op.Opcode.ADDI.value)

def execute():
    pass

def memory_access():
    pass

def write_back():
    pass


def register_dump():
    reg_names = ["x" + str(i) for i in range(32)] + ["PC"]
    file = []
    for i in range(len(reg_names)):
        if i != 0 and i % 8 == 0:
            file += "\n"
        file += " %3s: %08x" % (reg_names[i], regfile[i])
    print(''.join(file))


if __name__ == "__main__":
    with open('add1.o', 'r') as f:
        reset()
        lines = f.read().splitlines()
        instr_bytes = []
        for word in lines:
            instr_bytes.extend(word.split(" "))
        for i, byte in enumerate(instr_bytes):
            memory[i] = int(byte, 2)
    
    print(memory[regfile[PC]:regfile[PC]+4])
    instruction = fetch()
    print(instruction.bin)
    print('00000001000100001000000010010011')
    decode(instruction)
    regfile[PC] += 4
    register_dump()


