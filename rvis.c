#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <elf.h>

//custom headers
#include "elfreader.h" // contains get_segment_data() and Elfinfo data type
#include "rv32.h"
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
            puts("\n");
    }
}

void loader(ELFinfo elf, byte* segment_data, unsigned short segment_num) {
   Elf32_Addr address = elf.pheader[segment_num].p_paddr; 
   address -= elf.header.e_entry; // calculate offset
   if (address < 0 || address > MEM_SZ)
        exit(EXIT_FAILURE); 
   for (; address < elf.pheader[segment_num].p_filesz; ++address)
        memory[address] = segment_data[address]; 
}

word fetch(ELFinfo elf, word address) {
    address -= elf.header.e_entry; // calculate offset to index memory array
    word instruction = 0; // instruction of length 32 bits
    word instruction_bytes[4]; 
    for (int i = 0; i < 4; ++i) {
        instruction_bytes[i] = memory[address + i];
        //printf("instr: %x\n", instruction_bytes[i]);
        instruction_bytes[i] = instruction_bytes[i] << (i*8); // shift i bytes 
        instruction += instruction_bytes[i]; 
    }
    //printf("Instruction: %x\n", instruction);
    return instruction;
}

bitfields decode(word instruction) {
    bitfields encoding = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
    encoding.opcode = instruction & OPCODE;
    encoding.rd = instruction & RD;
    encoding.funct3 = instruction & FUNCT3;
    encoding.rs1 = instruction & RS1;
    encoding.rs2 = instruction & RS2;
    encoding.funct7 = instruction & FUNCT7;
    encoding.Itype = sign_extend((instruction & ITYPE) >> 20, 12);
    encoding.Stype = sign_extend(((instruction & STYPE_U) >> 20) |  ((instruction & STYPE_L) >> 7), 12);
    encoding.Btype = sign_extend((get_bits(1,32,instruction)<<12 | get_bits(1,8,instruction)<<11 | get_bits(6,26,instruction)<<5 | get_bits(4,9,instruction)<<1), 13);
    encoding.Utype = instruction & UTYPE;
    encoding.Jtype = sign_extend((get_bits(1,32,instruction)<<20 | get_bits(8,13,instruction)<<12 | get_bits(1,21,instruction)<<11 | get_bits(10,22,instruction)<<1), 21);
    
   //printf("Opcode: 0x%02x rd: 0x%02x funct3: 0x%01x rs1: 0x%02x rs2:  0x%02x funct7: 0x%02x\n", 
   //       encoding.opcode, encoding.rd, encoding.funct3, encoding.rs1, encoding.rs2, encoding.funct7);
   //printf("I: 0x%08x S: 0x%08x B: 0x%08x U: 0x%08x J: 0x%08x\n",
   //        encoding.Itype, encoding.Stype, encoding.Btype, encoding.Utype, encoding.Jtype);
    return encoding;
}



bool cycle(ELFinfo elf) {
    word instr = 0; 
    instr = fetch(elf,regfile[PC]);
    regfile[PC] += 4;
    bitfields encoding = decode(instr); 
    hart_dump();
    return false;
}

int main(){
    char elf_file[] = "riscv-tests/isa/rv32ui-p-beq";
    ELFinfo elf = read_elf(elf_file);
    for (int i=0; i<elf.num_pheaders; ++i)
        printf("%x\n", elf.header.e_entry);
    
    byte* segments_data[elf.header.e_phnum];
    for (size_t i = 0; i<elf.header.e_phnum; ++i) {
        segments_data[i] = get_segment_data(elf, i); 
        loader(elf, segments_data[i], i);
    }
    /*
    for (int i=0; i<elf.pheader[0].p_filesz; ++i) 
        printf("%0hhx", memory[i]); 
    puts("\n");
    for (int i=0; i<elf.pheader[1].p_filesz; ++i) 
        printf("%0hhx", memory[elf.pheader[0].p_filesz + i]); 
    puts("\n");
    */
    regfile[PC] = 0x80000174;
    unsigned int instr_count = 0; 
    for (int i=0; i<150; ++i)
        cycle(elf);
    //while(cycle(elf)){
    //    instr_count += 1;
    ////}

    free(elf.pheader);
    free(elf.buffer);
    for (int i=0; i<elf.num_pheaders; ++i)
        free(segments_data[i]);
    return EXIT_SUCCESS;
}
