#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <elf.h>

/*
#if defined(__LP64__)
#define ElfW(type) Elf64_ ## type
#else
#define ElfW(type) Elf32_ ## type
#endif
*/

#define PC 32; // program counter is index 32 in regfile

// Custom types
typedef unsigned char byte;
typedef uint32_t word;
typedef struct {
    Elf32_Ehdr header;  // Either Elf64_Ehdr or Elf32_Ehdr depending on architecture.
    Elf32_Phdr pheader; 
    byte* buffer; // stores elf data 
    long length; // specifies # of bytes in elf file
} elf_info;

// GLOBAL VARIABLES
byte memory[0x1000000]; // 16 MB of memory
word regfile[33];

elf_info read_elf_header(const char* elf_file) {
    elf_info info;
    info.buffer = NULL;
    FILE* file = fopen(elf_file, "rb");
    if(file) {
        // read the header
        fread(&info.header, sizeof(info.header), 1, file); // read file header, which starts at 0x0
        fseek(file, info.header.e_phoff, SEEK_SET); // set file to position of program header identified by e_phoff 
        fread(&info.pheader, sizeof(info.pheader), 1, file); // read program header starting at e_phoff
        if (memcmp(info.header.e_ident, ELFMAG, SELFMAG) == 0) { // check if it's an elf file
            fseek(file, 0, SEEK_END); // look for end of elf to get length in bytes
            info.length = ftell(file); // set length of elf file
            fseek(file, 0, SEEK_SET);
            info.buffer = malloc(info.length);
            if (info.buffer) {
                fread(info.buffer, 1, info.length, file);
            }
        }
        else
            exit(EXIT_FAILURE);
    }
    fclose(file);
    return info;
}

void reset() {
   memset(memory, 0, sizeof(memory)); 
   memset(regfile, 0, sizeof(regfile));
}

int main(){
    char elf_file[] = "riscv-tests/isa/rv32ui-p-add";
    elf_info elf = read_elf_header(elf_file);
    //printf("%02x\n", elf.header.e_phoff);
    int x = elf.header.e_phoff + elf.header.e_phentsize;
    //printf("%d\n", x);
    //printf("%u\n", elf.pheader.p_offset);
    int y = elf.header.e_phoff + elf.header.e_phentsize;
    //printf("%d\n", y);
    printf("%x\n", elf.buffer[elf.header.e_phoff + 0x04]);    
    printf("%x\n", elf.buffer[elf.header.e_phoff + 0x05]); 
    printf("%x\n", elf.buffer[elf.header.e_phoff + 0x06]); 
    printf("%x\n", elf.buffer[elf.header.e_phoff + 0x07]); 
    Elf32_Phdr pheader1; 
    printf("%x\n", elf.buffer[y + 0x04]);    
    printf("%x\n", elf.buffer[y + 0x05]); 
    printf("%x\n", elf.buffer[y + 0x06]); 
    printf("%x\n", elf.buffer[y + 0x07]); 
    //printf("%u\n", elf.header.e_phentsize);
    //printf("%u\n", elf.pheader.p_type);
    //printf("%02x\n", elf.buffer[elf.pheader.p_offset]);
    //for (int i=x; i<x+20; ++i) 
    //    printf("%02x\n", elf.buffer[i]);
    //for (uint i=elf.pheader.p_offset; i<elf.pheader.p_offset + elf.pheader.p_filesz; ++i) {
     //  printf("%hhx\t", elf.buffer[i]); 
    //}
    puts("\n");
    return EXIT_SUCCESS;
}
