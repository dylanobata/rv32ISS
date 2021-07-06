#! /usr/bin/env python3

# single cycle datapath RISC-V 32I
# Stages of RISCV datapath:
    # fetch
    # decode
    # execute
    # memory access
    # register writeback

# import argparse
import glob
from enum import Enum

from bitstring import Bits, BitArray
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
    SYSTEM = BitArray(bin = '0b1110011') 


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
        elif key == PC:
            self.registers[key] = value & 0xFFFFFFFF # store only the lowest 4 bytes
        else:    
            value = value & 0xFFFFFFFF # store only the lowest 4 bytes
            self.registers[key] = BitArray(value.to_bytes(4, "big"))


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


def hart_dump():
    reg_names = ["x" + str(i) for i in range(32)] + ["PC"] 
    file = [] 
    for i in range(len(reg_names)):
        if i != 0 and i % 8 == 0:
            file += "\n"
        if type(regfile[i]) == int:
            file += " %4s:0x%08x" % (reg_names[i], regfile[i])
        else:
            file += " %4s:0x%08x" % (reg_names[i], regfile[i].int)
    print(''.join(file))


def sign_extend(sign, bits): 
    return Bits(bool = sign)*(32 - len(bits)) + bits


def fetch(address):
    address -= 0x80000000 
    return BitArray(uint = int.from_bytes(memory[address:address+4], byteorder = "little"), length = 32)


def decode(instruction):
    opcode = Opcode(instruction[25:]) # 7 bits
    rd = instruction[20:25] # set up write
    src1 = instruction[12:17] # read rs1 into temp regsiter 
    src2 = instruction[7:12] # read rs2 into temp register
    funct3 = instruction[17:20]
    funct7 = instruction[0:7]
    imm_I = sign_extend(instruction[0], instruction[0:11])
    imm_S = sign_extend(instruction[0], instruction[0:7] + instruction[20:25])
    imm_B = sign_extend(instruction[0], (bin(instruction[0]) + bin(instruction[24]) + instruction[1:7] + instruction[20:24]) << 1) # shift left to access even locations only
    imm_U = sign_extend(instruction[0], instruction[0:20] << 12) 
    imm_J = sign_extend(instruction[0], (bin(instruction[0]) + instruction[12:20] + bin(instruction[11]) + instruction[1:11]) << 1) 
    print(instruction.bin, opcode)
    print(opcode, rd, src1, src2, funct3, funct7, imm_I, imm_S, imm_B, imm_U, imm_J)
    return opcode, rd, src1, src2, funct3, funct7, imm_I, imm_S, imm_B, imm_U, imm_J
  

def execute(opcode, rs1, rs2, funct3, funct7, imm_I, imm_S, imm_B, imm_U, imm_J, returnPC):
    
    def arithmetic(funct3, src1, src2, funct7=None):
        if funct3 == Funct3.ADD: # Add, AddI, Sub
            return src1.int - src2.int if funct7 == Funct7.SUB else src1.int + src2.int 
        if funct3 == Funct3.AND: # And, AndI
            return src1.int & src2.int
        if funct3 == Funct3.OR: # Or, OrI
            return src1.int | src2.int
        if funct3 == Funct3.XOR: # Xor, XorI
            return src1.int ^ src2.int
        if funct3 == Funct3.SRL: # srl, srli, sra, srai
            return (src1 >> src2.int).int if funct7 == Funct7.SRL else src1.int >> src2.int # sra, srai 
        if funct3 == Funct3.SLL: # sll, slli
            return src1.int << src2.int
        if funct3 == Funct3.SLT: # slt, slti
            return 1 if src1.int << src2.int else 0 
        if funct3 == Funct3.SLTU:
            return 1 if src.uint << src2.uint else 0
    
    def logic(funct3, src1, src2, imm_B, returnPC):
        if funct3 == Funct3.BEQ:
            return returnPC + imm_B.int if src1 == src2 else returnPC + 4 
        if funct3 == Funct3.BNE:
            return returnPC + imm_B.int if src1 != src2 else returnPC + 4 
        if funct3 == Funct3.BLT:
            return returnPC + imm_B.int if src1.int < src2.int else returnPC + 4 
        if funct3 == Funct3.BGE:
            return returnPC + imm_B.int if src1.int >= src2.int else returnPC + 4 
        if funct3 == Funct3.BLTU:
            return returnPC + imm_B.int if src1.uint < src2.uint else returnPC + 4
        if funct3 == Funct3.BGEU:
            return returnPC + imm_B.int if src1.uint >= src2.uint else returnPC + 4
            
    if opcode == Opcode.LUI:
        ALUOut = (imm_U + BitArray('0x0000')).int
    elif opcode == Opcode.AUIPC:
        ALUOut = returnPC + imm_U.int 
    elif opcode == Opcode.JAL:
        ALUOut = returnPC + imm_J.int
    elif opcode == Opcode.JALR:
        ALUOut = int(arithmetic(Funct3.ADD, rs1, imm_I))
    elif opcode == Opcode.BRANCH:
        funct3 = Funct3(funct3)
        ALUOut = int(logic(funct3, rs1, rs2, imm_B, returnPC))
    elif opcode == Opcode.LOAD:
        ALUOut = int(arithmetic(Funct3.ADD, rs1, imm_I)) 
    elif opcode == Opcode.STORE:
        ALUOut = int(arithmetic(Funct3.ADD, rs1, imm_S))
    elif opcode == Opcode.IMM:
        funct3 = Funct3(funct3)
        if funct3 in {Funct3.SLLI, Funct3.SRLI, Funct3.SRAI}:
            funct7 = Funct7(funct7)
        else:
            funct7 = None
        ALUOut = int(arithmetic(funct3=funct3, funct7=funct7, src1=rs1, src2=imm_I))
    elif opcode == Opcode.OP:
        funct3 = Funct3(funct3)
        funct7 = Funct7(funct7)
        ALUOut = int(arithmetic(funct3=funct3, funct7=funct7, src1=rs1, src2=rs2))
    elif opcode == Opcode.MISCMEM:
        return None 
    elif opcode == Opcode.SYSTEM:
        funct3 = Funct3(funct3)
        if funct3 != Funct3.ECALL:
            return None 
        if funct3 == Funct3.ECALL:
            print("  ecall", regfile[3])
            if regfile[3] > 1:
                raise Exception("FAILURE IN TEST")
            elif regfile[3] == 1:
                # hack for test exit
                return False
    return int(ALUOut)


def memory_access(opcode, funct3, ALUOut, rs2):
    if opcode == Opcode.STORE:
        MEMregister = None
        if funct3 == Funct3.SB:
            loader(rs2 & 0xFF, ALUOut)
        elif funct3 == Funct3.SH: 
            loader(rs2 & 0xFFFF, ALUOut)
        elif funct3 == Funct3.SW:
            loader(rs2 & 0xFFFFFFFF, ALUOut)
    elif opcode == Opcode.LOAD: 
        data = fetch(ALUOut).int
        if funct3 == Funct3.LB:
            MEMregister = sign_extend(data[0], data & 0xFF) 
        elif funct3 == Funct3.LBU:
            MEMregister = sign_extend(0, data & 0xFF) 
        elif funct3 == Funct3.LHU:
            MEMregister = sign_extend(0, data & 0xFFFF) 
        elif funct3 == Funct3.LH:
            MEMregister = sign_extend(data[0], data & 0xFFFF) 
        elif funct3 == Funct3.LW:
            MEMregister = sign_extend(data[0], data & 0xFFFFFFFF) 
    return MEMregister


def write_back(rd, write_data):
    regfile[rd.uint] = write_data 


def cycle() -> bool:
    # Fetch
    instruction = fetch(regfile[PC])
    print(instruction)

    # Decode
    opcode, rd, src1, src2, funct3, funct7, I, S, B, U, J = decode(instruction) 
    returnPC = regfile[PC] # set up return address for PC
    PCNext = regfile[PC] + 4
    mem_op = opcode in {Opcode.LOAD, Opcode.STORE} # check if need to store in memory
    write_op = opcode in {Opcode.LOAD, Opcode.OP, Opcode.IMM, Opcode.LUI, Opcode.JAL, Opcode.JALR, Opcode.AUIPC}  # check if need to write to memory
    print(opcode, rd, funct3, funct7, I, S, B, U, J)
 
    # Execute
    ALUOut = execute(opcode, src1, src2, funct3, funct7, I, S, B, U, J, returnPC)
    print(ALUOut) 
    
    # Memory access
    if mem_op:
      MEMregister = memory_access(Funct3(funct3), ALUOut, src2) 
    
    # Write back
    if write_op:
        if opcode == Opcode.LOAD:
            write_back(rd, MEMregister)
        else:
            write_back(rd, ALUOut)
    hart_dump()

    # Calculate PC
    if opcode in {Opcode.BRANCH, Opcode.JAL, Opcode.JALR, Opcode.AUIPC}:
       regfile[PC] = ALUOut 
    else:
        regfile[PC] = PCNext 
    return True


if __name__ == "__main__":
    for test_file in sorted(glob.glob("riscv-tests/isa/rv32ui-p-*")):
        if test_file.endswith('.dump'):
            continue
        with open(test_file, 'rb') as f:
            elf_file = ELFFile(f)
            print(test_file, ":")
            reset() # reset memory and PC for next program 
            regfile[PC] = 0x80000000  
            # ELF loader loads program into memory at location 0x80000000 
            for segment in elf_file.iter_segments(): 
                loader(segment.data(), segment.header.p_paddr) 
           #     print(memory[:len(segment.data())]) 
            instruction_count = 0 
            while cycle():
                instruction_count += 1
            print("  ran %d instructions" % instruction_count) 
            exit(0)
