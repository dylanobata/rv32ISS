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
        else:
            self.registers[key] = value & 0xFFFFFFFF # store only the lowest 4 bytes


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
    reg_names = \
        ['x0', 'ra', 'sp', 'gp', 'tp'] + ['t%d'%i for i in range(0,3)] + ['s0', 's1'] +\
        ['a%d'%i for i in range(0,8)] +\
        ['s%d'%i for i in range(2,12)] +\
        ['t%d'%i for i in range(3,7)] + ["PC"]
    file = [] 
    for i in range(len(reg_names)):
        if i != 0 and i % 8 == 0:
            file += "\n"
        if type(regfile[i] == int) and i == 32:
            file += " %4s:0x%08x" % (reg_names[i], regfile[i])
        else:
            file += " %4s:0x%08x" % (reg_names[i], regfile[i])
    print(''.join(file), '\n')


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
    imm_I = sign_extend(instruction[0], instruction[0:12])
    imm_S = sign_extend(instruction[0], instruction[0:7] + instruction[20:25])
    imm_B = sign_extend(instruction[0], (bin(instruction[0]) + bin(instruction[24]) + instruction[1:7] + instruction[20:24]) << 1) # shift left to access even locations only
    imm_U = instruction[0:20] + BitArray('0x000') 
    imm_J = sign_extend(instruction[0], (bin(instruction[0]) + instruction[12:20] + bin(instruction[11]) + instruction[1:11]) << 1) 
    #print(instruction.bin, opcode)
    return opcode, rd, src1, src2, funct3, funct7, imm_I, imm_S, imm_B, imm_U, imm_J
  

def execute(opcode, rs1, rs2, funct3, funct7, imm_I, imm_S, imm_B, imm_U, imm_J, returnPC):
    
    def arithmetic(funct3, src1, src2, funct7=None):
        if funct3 == Funct3.ADD: # Add, AddI, Sub
            return src1 - src2 if funct7 == Funct7.SUB else src1 + src2
        if funct3 == Funct3.AND: # And, AndI
            return src1 & src2
        if funct3 == Funct3.OR: # Or, OrI
            return src1 | src2
        if funct3 == Funct3.XOR: # Xor, XorI
            return src1 ^ src2
        if funct3 == Funct3.SRL: # srl, srli, sra, srai
            return src1 >> (src2 % 32) if funct7 == Funct7.SRL else BitArray(hex(src1)).int >> (src2 % 32) # sra, srai 
        if funct3 == Funct3.SLL: # sll, slli
            return src1 << (src2 % 32) # max shift amount is in range [0,31] bits
        if funct3 == Funct3.SLT: # slt, slti
            #print("src1: ", src1, "src2: ", src2)
            src1 = BitArray(hex(src1 & 0xFFFFFFFF))
            src2 = BitArray(hex(src2 & 0xFFFFFFFF))
            src1 = BitArray(sign_extend(0, src1))
            src2 = BitArray(sign_extend(0, src2))
            return 1 if src1.int < src2.int else 0 
        if funct3 == Funct3.SLTU:
            #print("src1: ", src1, "src2: ", src2)
            src1 = BitArray(hex(src1 & 0xFFFFFFFF))
            src2 = BitArray(hex(src2 & 0xFFFFFFFF))
            src1 = BitArray(sign_extend(0, src1))
            src2 = BitArray(sign_extend(0, src2))
            return 1 if src1.uint < src2.uint else 0 

    def logic(funct3, src1, src2, imm_B, returnPC):
        if funct3 == Funct3.BEQ:
            return returnPC + imm_B if src1.int == src2.int else returnPC + 4 
        if funct3 == Funct3.BNE:
            return returnPC + imm_B if src1.int != src2.int else returnPC + 4 
        if funct3 == Funct3.BLT:
            return returnPC + imm_B if src1.int < src2.int else returnPC + 4 
        if funct3 == Funct3.BGE:
            return returnPC + imm_B if src1.int >= src2.int else returnPC + 4 
        if funct3 == Funct3.BLTU:
            return returnPC + imm_B if src1.uint < src2.uint else returnPC + 4
        if funct3 == Funct3.BGEU:
            return returnPC + imm_B if src1.uint >= src2.uint else returnPC + 4
            
    if opcode == Opcode.LUI:
        ALUOut = (imm_U).int
    elif opcode == Opcode.AUIPC:
        ALUOut = returnPC + imm_U.int 
    elif opcode == Opcode.JAL:
        ALUOut = returnPC + imm_J.int
    elif opcode == Opcode.JALR:
        ALUOut = int(arithmetic(Funct3.ADD, regfile[rs1.uint], imm_I.int))
    elif opcode == Opcode.BRANCH:
        funct3 = Funct3(funct3)
        ALUOut = int(logic(funct3, BitArray(hex(regfile[rs1.uint])), BitArray(hex(regfile[rs2.uint])), imm_B.int, returnPC))
    elif opcode == Opcode.LOAD:
        ALUOut = int(arithmetic(Funct3.ADD, regfile[rs1.uint], imm_I.int)) 
    elif opcode == Opcode.STORE:
        ALUOut = int(arithmetic(Funct3.ADD, regfile[rs1.uint], imm_S.int))
    elif opcode == Opcode.IMM:
        funct3 = Funct3(funct3)
        if funct3 in {Funct3.SLLI, Funct3.SRLI, Funct3.SRAI}:
            funct7 = Funct7(funct7)
            ALUOut = int(arithmetic(funct3=funct3, funct7=funct7, src1=regfile[rs1.uint], src2=rs2.uint))
        else:
            funct7 = None
            ALUOut = int(arithmetic(funct3=funct3, funct7=funct7, src1=regfile[rs1.uint], src2=imm_I.int))
    elif opcode == Opcode.OP:
        funct3 = Funct3(funct3)
        funct7 = Funct7(funct7)
        ALUOut = int(arithmetic(funct3=funct3, funct7=funct7, src1=regfile[rs1.uint], src2=regfile[rs2.uint]))
    elif opcode == Opcode.MISCMEM:
        return None 
    elif opcode == Opcode.SYSTEM:
        funct3 = Funct3(funct3)
        if funct3 != Funct3.ECALL:
            return None 
        if funct3 == Funct3.ECALL:
        # hack for test exit
            return False
    return int(ALUOut)


def memory_access(opcode, funct3, ALUOut, src2):
    if opcode == Opcode.STORE:
        MEMregister = None
        if funct3 == Funct3.SB:
            loader((src2 & 0xff).to_bytes(1,byteorder='little'), ALUOut)
        elif funct3 == Funct3.SH: 
            loader((src2 & 0xffff).to_bytes(2,byteorder='little'), ALUOut)
        elif funct3 == Funct3.SW:
            loader((src2 & 0xffffffff).to_bytes(4,byteorder='little') , ALUOut)
        return MEMregister
    elif opcode == Opcode.LOAD: 
        data = fetch(ALUOut)
        if funct3 == Funct3.LB:
            MEMregister = sign_extend(data[0], data & '0x000000FF') 
        elif funct3 == Funct3.LBU:
            MEMregister = sign_extend(0, data & '0x000000FF') 
        elif funct3 == Funct3.LHU:
            MEMregister = sign_extend(0, data & '0x0000FFFF') 
        elif funct3 == Funct3.LH:
            MEMregister = sign_extend(data[0], data & '0x0000FFFF') 
        elif funct3 == Funct3.LW:
            MEMregister = sign_extend(data[0], data & '0xFFFFFFFF')
        return MEMregister.int


def write_back(rd, write_data):
    regfile[rd.uint] = write_data 


def cycle() -> bool:
    # Fetch
    instruction = fetch(regfile[PC])
    #print(instruction)
    
    # Decode
    opcode, rd, src1, src2, funct3, funct7, I, S, B, U, J = decode(instruction) 
    #print("Opcode:", opcode, "rd:", rd, "rs1", src1, "rs2:", src2, "funct3:", funct3, "funct7:", funct7, "imm_I:", I, "imm_S:", S, "imm_B:", B, "imm_U:", U, "imm_J:", J)
    returnPC = regfile[PC] # set up return address for PC
    PCNext = regfile[PC] + 4
    mem_op = opcode in {Opcode.LOAD, Opcode.STORE} # check if need to store in memory
    write_op = opcode in {Opcode.LOAD, Opcode.OP, Opcode.IMM, Opcode.LUI, Opcode.JAL, Opcode.JALR, Opcode.AUIPC}  # check if need to write to memory
 
    # Execute
    ALUOut = execute(opcode, src1, src2, funct3, funct7, I, S, B, U, J, returnPC)
    #if ALUOut != None: print('ALUOut', hex(ALUOut)) 
    
    # Memory access
    if mem_op:
      MEMregister = memory_access(opcode, Funct3(funct3), ALUOut, regfile[src2.uint]) 
    
    # Write back
    if write_op:
        if opcode == Opcode.LOAD:
            write_back(rd, MEMregister)
        elif opcode in {Opcode.JAL, Opcode.JALR}:
            write_back(rd, regfile[PC]+4)
        else:
            write_back(rd, ALUOut)
    #hart_dump()

    # Calculate PC
    if opcode in {Opcode.BRANCH, Opcode.JAL, Opcode.JALR}:
       regfile[PC] = ALUOut   
    else:
        regfile[PC] = PCNext 
    
    # test if program is done 
    if ALUOut == False and type(ALUOut) == bool:
        return False
    else:
        return True


if __name__ == "__main__":
    for test_file in sorted(glob.glob("riscv-tests/isa/rv32ui-p-*")):
        if test_file.endswith('.dump') or test_file.endswith('fence_i'):
            continue
        with open(test_file, 'rb') as f:
            elf_file = ELFFile(f)
            print(test_file, ":")
            reset() # reset memory and PC for next program 
            regfile[PC] = 0x80000000  
            # ELF loader loads program into memory at location 0x80000000 
            for segment in elf_file.iter_segments(): 
                loader(segment.data(), segment.header.p_paddr) 
            instruction_count = 0 
            regfile[PC] = 0x80000174 # skip straight to instruction tests, ignoring csr instructions 
            while cycle():
                instruction_count += 1
             
            instruction = fetch(regfile[PC])
            print(hex(regfile[PC]))
            print(instruction.hex)
            if instruction.hex == 'c0001073':
                print("PASS") 
            else:
                print("FAIL")
            print("ran %d instructions\n" % instruction_count) 
            #exit(0)
