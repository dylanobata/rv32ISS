#ifndef ELFREADER
#define ELFREADER

#include <elf.h>
#include <stddef.h>

typedef unsigned char byte;
typedef uint32_t word;

typedef struct {
    Elf32_Ehdr header;
    Elf32_Phdr* pheader;
    unsigned short num_pheaders;
    byte* buffer;
    long length;
} ELFinfo;

ELFinfo read_elf(const char*);
byte* get_segment_data(ELFinfo, size_t);
#endif
