#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <elf.h>
#include "elfreader.h"

#define PC 32 // program counter is index 32 in regfile
#define MEM_SZ  0x1000000

// GLOBAL VARIABLES
byte memory[MEM_SZ]; // 16 MB of memory, starting at 0x80000000
word regfile[33];

void reset() {
   memset(memory, 0, sizeof(memory)); 
   memset(regfile, 0, sizeof(regfile));
}

void loader(ELFinfo elf, byte* segment_data, unsigned short segment_num) {
   Elf32_Addr address = elf.pheader[segment_num].p_paddr; 
   address -= elf.header.e_entry;
   if (address < 0 || address > MEM_SZ)
        exit(EXIT_FAILURE); 
   for (; address< elf.pheader[segment_num].p_filesz; ++address)
        memory[address] = segment_data[address]; 
}

int main(){
    char elf_file[] = "riscv-tests/isa/rv32ui-p-add";
    ELFinfo elf = read_elf(elf_file);
    for (int i=0; i<elf.num_pheaders; ++i)
        printf("%x\n", elf.header.e_entry);
    byte* segments_data[elf.header.e_phnum];
    for (size_t i=0; i<elf.header.e_phnum; ++i) {
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
   
    free(elf.pheader);
    free(elf.buffer);
    for (int i=0; i<elf.num_pheaders; ++i)
        free(segments_data[i]);
    return EXIT_SUCCESS;
}
