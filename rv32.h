#ifndef RV32
#define RV32

#include "elfreader.h"

typedef uint32_t word;

#define OPCODE   0b00000000000000000000000001111111
#define RD       0b00000000000000000000111110000000 
#define FUNCT3   0b00000000000000000111000000000000 
#define RS1      0b00000000000011111000000000000000 
#define RS2      0b00000001111100000000000000000000 
#define FUNCT7   0b11111110000000000000000000000000 
#define ITYPE    0b11111111111111110000000000000000 
#define STYPE_U  0b11111110000000000000000000000000 
#define STYPE_L  0b00000000000000000000111110000000
#define UTYPE    0b11111111111111111111000000000000 

enum FieldID {
    LUI = 0b0110111, // load upper immediate
    AUIPC = 0b0010111, // Add upper immediate to PC 
    JAL = 0b1101111, // Jump and link 
    JALR = 0b1100111, // Jump and link register
    BRANCH = 0b1100011,
    LOAD = 0b0000011,
    STORE = 0b0100011,
    IMM = 0b0010011,// Immediate instructions
    OP = 0b0110011, // Arithmetic/Logic Ops 
    MISCMEM = 0b0001111,
    SYSTEM = 0b1110011, 

    F3_JALR = 0b000,
    F3_BEQ = 0b000,
    F3_LB = 0b000,
    F3_SB = 0b000,
    F3_ADDI = 0b000,
    F3_ADD = 0b000,
    F3_SUB = 0b000,
    F3_FENCE = 0b000,
    F3_ECALL = 0b000,
    F3_EBREAK = 0b000,
    
    F3_BNE = 0b001,
    F3_LH = 0b001,
    F3_SH = 0b001,
    F3_SLLI = 0b001,
    F3_SLL = 0b001,
    F3_FENCEI = 0b001,
    F3_CSRRW = 0b001,

    F3_BLT = 0b100,
    F3_LBU = 0b100,
    F3_XORI = 0b100,
    F3_XOR = 0b100,

    F3_BGE = 0b101,
    F3_LHU = 0b101,
    F3_SRLI = 0b101,
    F3_SRAI = 0b101,
    F3_SRL = 0b101,
    F3_SRA = 0b101,
    F3_CSRRWI = 0b101,

    F3_BLTU = 0b110,
    F3_ORI = 0b110,
    F3_OR = 0b110,
    F3_CSRRSI = 0b110,

    F3_BGEU = 0b111,
    F3_ANDI = 0b111,
    F3_AND = 0b111,
    F3_CSRRCI = 0b111,
    
    F3_LW = 0b010,
    F3_SW = 0b010,
    F3_SLTI = 0b010,
    F3_SLT = 0b010,
    F3_CSRRS = 0b010,
    
    F3_SLTIU = 0b011,
    F3_SLTU = 0b011,
    F3_CSRRC = 0b011,
    
    F7_SRAI = 0b0100000,
    F7_SUB = 0b0100000,
    F7_SRA = 0b0100000,
    
    F7_SLLI = 0b0000000,
    F7_SRLI = 0b0000000,
    F7_ADD = 0b0000000,
    F7_SLL = 0b0000000,
    F7_SLT = 0b0000000,
    F7_SLTU = 0b0000000,
    F7_XOR = 0b0000000,
    F7_SRL = 0b0000000,
    F7_OR = 0b0000000,
    F7_AND = 0b0000000
};

typedef struct bitfields{
    word opcode, rd, rs1, rs2, funct3, funct7, Itype, Stype, Btype, Utype, Jtype;
} bitfields;

#endif
