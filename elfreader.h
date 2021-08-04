#ifndef ELFREADER
#define ELFREADER

#include <elf.h>
#include <stddef.h>
#include <stdio.h>

typedef unsigned char byte;

typedef struct {
    Elf32_Ehdr header;
    Elf32_Phdr* pheader;
    unsigned short num_pheaders;
    byte* buffer;
    long length;
} ELFinfo;

ELFinfo read_elf(const char* elf_file) {
    ELFinfo info;
    info.buffer = NULL;
    FILE* file = fopen(elf_file, "rb");
    if(file) {
        fread(&info.header, sizeof(info.header), 1, file); // read file header, which starts at 0x0
        info.pheader = malloc(sizeof(Elf32_Phdr)*info.header.e_phnum);
        info.num_pheaders = info.header.e_phnum;
        for (uint16_t i=0; i<info.num_pheaders; ++i) {
            fseek(file, info.header.e_phoff + sizeof(Elf32_Phdr)*i, SEEK_SET);
            fread(&info.pheader[i], sizeof(Elf32_Phdr), 1, file);
        }
        if (memcmp(info.header.e_ident, ELFMAG, SELFMAG) == 0) { // check if it's an elf file
            fseek(file, 0, SEEK_END); // look for end of elf to get length in bytes
            info.length = ftell(file); // set length of elf file
            fseek(file, 0, SEEK_SET);
            info.buffer = malloc(info.length);
            if (info.buffer) 
                 fread(info.buffer, 1, info.length, file);
            
         }
         else
             exit(EXIT_FAILURE);
     }
     fclose(file);
     return info;
}

byte* get_segment_data(ELFinfo elf, size_t segment_num) {
    byte* segment_buffer;
    segment_buffer = malloc(elf.pheader[segment_num].p_filesz);
    for (uint32_t i=0; i<elf.pheader[segment_num].p_filesz; ++i)
        segment_buffer[i] = elf.buffer[elf.pheader[segment_num].p_offset + i];
    return segment_buffer;
}

#endif
