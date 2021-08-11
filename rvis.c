#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <elf.h>

//custom headers
#include "elfreader.h" // contains get_segment_data() and Elfinfo data type
#include "rv32.h" // bitfields data type 
#include "bitmanip.h" // contains sign_extend() and get_bit()

#define PC 32 // program counter is index 32 in regfile
#define MEM_SZ  0x1000000 // 16 MB of memory

// GLOBAL VARIABLES
byte memory[MEM_SZ]; // starts at 0x80000000
word regfile[33]; // 32, 32 bit word general purpose registers for RV32 and 1 32 bit register for the program counter

void reset() {
   memset(memory, 0, sizeof(memory)); 
   memset(regfile, 0, sizeof(regfile));
}

void hart_dump() {
    char reg_names[][33] = {
        "x0", "ra", "sp", "gp", "tp", "t0", "t1", "t2", 
        "s0", "s1", "a0", "a1", "a2", "a3", "a4", "a5",
        "a6", "a7", "s2", "s3", "s4", "s5", "s6", "s7",
        "s8", "s9", "s10", "s11", "t3", "t4", "t5", "t6",
        "PC" };
    for (int i=0; i<33; ++i) {
        if (i%6 == 0) 
            puts("\n");
        printf("%s:0x%08x\t", reg_names[i], regfile[i]);
        if (i == 32)
            puts("\n\n");
    }
}

void loader(ELFinfo elf, byte* segment_data, unsigned short segment_num) {
    Elf32_Addr address = elf.pheader[segment_num].p_paddr; 
    address -= elf.header.e_entry; // calculate offset
    if (address < 0 || address > MEM_SZ) {
         puts("LOAD FAIL"); 
         exit(EXIT_FAILURE);
    }
    printf("Address: %x\n", address); 
    for (size_t i=0; i < elf.pheader[segment_num].p_filesz; ++address, ++i) {
        memory[address] = segment_data[i];
   }
   puts("\n");
}

word fetch(word address, Elf32_Addr entry) {
    //word address = regfile[PC]; 
    address -= entry; // calculate offset to index memory array
    word instruction = 0; // instruction of length 32 bits
    word instruction_bytes[4]; // instructions come in 4 bytes for 32 bit arch
    if (address < 0 || address > MEM_SZ) {
        puts("FETCH FAILED"); 
        exit(EXIT_FAILURE);
    }
    for (int i = 0; i < 4; ++i) {
        instruction_bytes[i] = memory[address + i];
        instruction_bytes[i] = instruction_bytes[i] << (i*8); // shift i bytes 
        instruction += instruction_bytes[i]; 
    }
    //printf("Instruction: %x\n", instruction);
    return instruction;
}

bitfields decode(word instruction) {
// decode instruction following RISC-V 32 bit instruction format
    bitfields encoding = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
    encoding.opcode = instruction & OPCODE;
    encoding.rd = (instruction & RD) >> 7;
    encoding.funct3 = (instruction & FUNCT3) >> 12;
    encoding.rs1 = (instruction & RS1) >> 15;
    encoding.rs2 = (instruction & RS2) >> 20;
    encoding.funct7 = (instruction & FUNCT7) >> 25;
    encoding.Itype = sign_extend((instruction & ITYPE) >> 20, 12);
    encoding.Stype = sign_extend(((instruction & STYPE_U) >> 20) |  ((instruction & STYPE_L) >> 7), 12);
    encoding.Btype = sign_extend((get_bits(1,32,instruction)<<12 | get_bits(1,8,instruction)<<11 | get_bits(6,26,instruction)<<5 | get_bits(4,9,instruction)<<1), 13);
    encoding.Utype = instruction & UTYPE;
    encoding.Jtype = sign_extend((get_bits(1,32,instruction)<<20 | get_bits(8,13,instruction)<<12 | get_bits(1,21,instruction)<<11 | get_bits(10,22,instruction)<<1), 21);
    return encoding;
}

word arithmetic(word funct3, bitfields encoding, word src2) { // src2 is either a 2nd register or an immediate 
    switch (funct3) {
        case F3_ADD: 
            if (encoding.funct7 == F7_SUB)
                return regfile[encoding.rs1] - src2;
            else return regfile[encoding.rs1] + src2;
        case F3_AND:
            return regfile[encoding.rs1] & src2;
        case F3_OR:
            return regfile[encoding.rs1] | src2;
        case F3_XOR:
            return regfile[encoding.rs1] ^ src2;
        case F3_SRL:
            if (encoding.funct7 == F7_SRL)
                return regfile[encoding.rs1] >> (src2 % 32);
            else
                return (int32_t)regfile[encoding.rs1] >> (src2 % 32); // sra and srai
        case F3_SLL:
            return regfile[encoding.rs1] << (src2 % 32);
        case F3_SLT:
            if ((int32_t)regfile[encoding.rs1] < (int32_t)src2)
                return 1;
            else return 0;
        case F3_SLTU:
            if (regfile[encoding.rs1] < src2)
                return 1;
            else return 0; 
        default:
            return 0;
    }
}

word logic(bitfields encoding) {
    switch (encoding.funct3) {
        case F3_BEQ:
            if ((int32_t)regfile[encoding.rs1] == (int32_t)regfile[encoding.rs2])
                return regfile[PC] + encoding.Btype;
            else return regfile[PC] + 4;
        case F3_BNE:
            if ((int32_t)regfile[encoding.rs1] != (int32_t)regfile[encoding.rs2])
                return regfile[PC] + encoding.Btype;
            else return regfile[PC] + 4;
        case F3_BLT:
            if ((int32_t)regfile[encoding.rs1] < (int32_t)regfile[encoding.rs2])
                return regfile[PC] + encoding.Btype;
            else return regfile[PC] + 4;
        case F3_BGE:
            if ((int32_t)regfile[encoding.rs1] >= (int32_t)regfile[encoding.rs2])
                return regfile[PC] + encoding.Btype;
            else return regfile[PC] + 4;
        case F3_BLTU:
            if (regfile[encoding.rs1] < regfile[encoding.rs2])
                return regfile[PC] + encoding.Btype;
            else return regfile[PC] + 4;
        case F3_BGEU:
            if (regfile[encoding.rs1] >= regfile[encoding.rs2])
                return regfile[PC] + encoding.Btype;
            else return regfile[PC] + 4;
        default:
            return 0;
    }
}

word execute(bitfields encoding) {
    switch (encoding.opcode) {
        case LUI:
            return (int32_t)encoding.Utype; 
             
        case AUIPC:
            //return regfile[PC] + (int32_t)encoding.Utype; 
        
        case JAL:
            return regfile[PC] + (int32_t)encoding.Jtype; 
        
        case JALR:
            return arithmetic(encoding.funct3, encoding, encoding.Itype);
        
        case BRANCH:
            return logic(encoding); 
        
        case LOAD:
            return arithmetic(F3_ADD, encoding, encoding.Itype);

        case STORE:
            return arithmetic(F3_ADD, encoding, encoding.Stype); 
        
        case IMM:
            if (encoding.funct3 == F3_SLLI || encoding.funct3 == F3_SRLI || encoding.funct3 == F3_SRAI)
                return arithmetic(encoding.funct3, encoding, encoding.rs2); 
            else return arithmetic(encoding.funct3, encoding, encoding.Itype);
        
        case OP:
            return arithmetic(encoding.funct3, encoding, regfile[encoding.rs2]);  
        
        case MISCMEM:
            return 0; 

        case SYSTEM:
            return 0;  
        
        default:
            return 0;
    } 
}

void load_byte(ELFinfo elf, word address, byte ALUout) {
    address -= elf.header.e_entry; // calculate offset
    if (address < 0 || address > MEM_SZ) {
        puts("LOAD_BYTE FAILED"); 
        exit(EXIT_FAILURE);
    }
    memory[address] = ALUout; 
}

word memory_access(ELFinfo elf, bitfields encoding, word ALUout) {
    word MEMregister = 0; 
    if (encoding.opcode == STORE) {
        if (encoding.funct3 == F3_SB) 
           load_byte(elf, ALUout, (regfile[encoding.rs2] & 0xFF)); 
         
        else if (encoding.funct3 == F3_SH) 
            for (unsigned char i=0; i<4; ++i)
                load_byte(elf, ALUout + i, ((regfile[encoding.rs2] & (0xFF << i*8)) >> i*8));
        
        else if (encoding.funct3 == F3_SW) 
            for (unsigned char i=0; i<4; ++i)
                load_byte(elf, ALUout + i, ((regfile[encoding.rs2] & (0xFF << i*8)) >> i*8));
    }
    else {
        word data = fetch(ALUout, elf.header.e_entry);
        printf("DATA: %x\n", data);
        if (encoding.funct3 == F3_LB)
            MEMregister = sign_extend((int32_t)data & 0xFF, 8);  
        
        else if (encoding.funct3 == F3_LBU)
            MEMregister = (byte)data;
        
        else if (encoding.funct3 == F3_LHU)
            MEMregister = data & 0xFFFF;
        
        else if (encoding.funct3 == F3_LH)
            MEMregister = sign_extend((int32_t)data & 0xFFFF, 16);
        
        else if (encoding.funct3 == F3_LW) 
            MEMregister = (int32_t)data; 
    }
    return MEMregister;
    
}

void write_back(bitfields encoding, word ALUout) {
    regfile[encoding.rd] = ALUout;
    regfile[0] = 0; // x0 is always 0 
}

bool cycle(ELFinfo elf) {
    // fetch  
    word instr = fetch(regfile[PC], elf.header.e_entry);
    printf("Instr: %x\n", instr);    
    
    // decode
    bitfields encoding = decode(instr);
    printf("Opcode: 0x%02x rd: 0x%02x rs1: 0x%02x rs2:  0x%02x funct3: 0x%01x funct7: 0x%02x\n", 
        encoding.opcode, encoding.rd, encoding.rs1, encoding.rs2, encoding.funct3,  encoding.funct7);
    printf("I: 0x%08x S: 0x%08x B: 0x%08x U: 0x%08x J: 0x%08x\n",
        encoding.Itype, encoding.Stype, encoding.Btype, encoding.Utype, encoding.Jtype);
     
    // execute
    word ALUout = execute(encoding);
    printf("ALUout: %x\n", ALUout);   
    
    // memory access
    word MEMregister = 0;
    if (encoding.opcode == LOAD || encoding.opcode == STORE){ 
        MEMregister = memory_access(elf, encoding, ALUout);
        printf("MEMregister: %x\n", MEMregister);
    }

    // write back
    if (encoding.opcode == LOAD || encoding.opcode == OP || encoding.opcode == IMM || 
        encoding.opcode == LUI || encoding.opcode == JAL || encoding.opcode == JALR || encoding.opcode == AUIPC) {
        
        if (encoding.opcode == LOAD) 
            write_back(encoding, MEMregister);
        
        else if (encoding.opcode == JAL || encoding.opcode == JALR) 
            write_back(encoding, regfile[PC] + 4);
        
        else {
            write_back(encoding, ALUout);
        }
    }
    
    // show register content
    hart_dump();
    
    // PC calculation
    if (encoding.opcode == BRANCH || encoding.opcode == JAL || encoding.opcode == JALR)
        regfile[PC] = ALUout;
    else regfile[PC] += 4;
    
    if (encoding.opcode == SYSTEM && encoding.funct3 == F3_ECALL) 
        return false;
    else return true;
}

int main(){
    char elf_file[] = "riscv-tests/isa/rv32ui-p-sh";
    ELFinfo elf = read_elf(elf_file);
    byte* segments_data[elf.header.e_phnum];
    for (size_t i = 0; i<elf.header.e_phnum; ++i) {
        segments_data[i] = get_segment_data(elf, i); 
        loader(elf, segments_data[i], i);
    }
    /* 
    for (int i=0; i<elf.pheader[0].p_filesz; ++i) 
        printf("%0hhx", memory[i]); 
    puts("\n"); */
//    for (int i=0; i<elf.pheader[1].p_filesz; ++i) 
//        printf("%0hhx", memory[elf.pheader[0].p_filesz + i]); 
//    puts("\n");
   

//    for (int i=0; i<elf.pheader[1].p_filesz; ++i)
//        printf("%0hhx", segments_data[1][i]);
//    puts("\n");
    regfile[PC] = 0x80000174;
    unsigned int instr_count = 0; 
    while(cycle(elf)){
        instr_count += 1;
    }
    //word instr = fetch(regfile[PC], elf.header.e_entry);
    //printf("PC: %x\n", regfile[PC]); 
    //printf("INSTR: %x\n", instr);
    printf("Ran: %d instructions\n", instr_count);
    //printf("MEMORY: %x\n", memory[0x1000]); 
    //for (int i=0; i<0x2050; i++)
    //    printf("ADDRESS: %x    Value: %x\n", i+0x80000000, memory[i]);

    free(elf.pheader);
    free(elf.buffer);
    for (int i=0; i<elf.num_pheaders; ++i)
        free(segments_data[i]);
    return EXIT_SUCCESS;
}
