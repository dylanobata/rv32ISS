from enum import Enum
from bitstring import BitArray

# RISC-V32I has 3 possible opcode fields. The last 7 bits of every instruction 
# are always the opcode. From there, depending on the type of instruction, there can be 
# extended opcode fields denoted by funct3 and funct7. The six types of instructions for
# RV32I are:
#   1. R-type   2. I-type   3. S-type   4. B-type   5. U-type   6. J-type

class Opcode(Enum):
    
    LUI = 0b0110111

    AUIPC = 0b0010111    
    
    JAL = 0b1101111
    
    JALR = 0b1100111

    # BRANCH OPS
    BEQ = BNE = \
    BLT = BGE = \
    BLTU = BGEU = 0b1100011
    
    # LOAD OPS
    LB = LH = \
    LW = LBU = \
    LHU = 0b0000011
    
    # STORE OPS
    SB = SH = SW = 0b0100011
    
    # IMMEDIATE OPS
    ADDI = SLTI = \
    SLTIU = XORI = \
    ORI = ANDI = \
    SLLI = SRLI = \
    SRAI = BitArray(bin = '0b0010011')

    # ARITHMETIC/LOGIC OPS
    ADD = SUB = \
    SLL = SLT = \
    SLTU = XOR = \
    SRL = SRA = \
    OR = AND = 0b0110011


    FENCE = FENCEI = 0b0001111

    ECALL = EBREAK = \
    CSRRW = CSRRS = \
    CSRRC = CSRRWI = \
    CSRRSI = CSRRCI = 0b1110011


class Funct3(Enum):
    JALR = BEQ = LB = \
    SB = ADDI = ADD = SUB = \
    FENCE = ECALL = EBREAK = 0b000
    
    BNE = LH = SH = \
    SLLI = SLL = FENCEI = CSRRW = 0b001

    BLT = LBU = XORI = XOR =0b100

    BGE = LHU = SRLI = SRAI = \
    SRL = SRA = CSRRWI = 0b101

    BLTU = ORI = OR = CSRRSI = 0b110

    BGEU = ANDI = AND = CSRRCI = 0b111
    
    LW = SW = SLTI = \
    SLT = CSRRS = 0b010
    
    SLTIU = SLTU = CSRRC = 0b011



class Funct7(Enum):
    SRAI = SUB = SRA = 0b0100000
    
    SLLI = SRLI = ADD = \
    SLL = SLT = SLTU = \
    XOR = SRL = OR = AND = 0b0000000