#ifndef BITMANIP
#define BITMANIP

#include <stdint.h>

int32_t get_bits(uint32_t bits, uint8_t start, uint8_t end) {
    // returns bits from [start, end) 
    return (bits >> end) & ((1 << (start-end+1))-1); 
}

int32_t sign_extend(uint32_t bits, unsigned num_bits) {
    if (bits >> (num_bits-1) == 1)
        return -((1 << num_bits) - bits);
    else
        return bits; 
}

void print_binary(uint32_t bits)
{
    for(int i=sizeof(bits) << 3; i; i--)
        putchar('0' + ((bits >> (i-1)) & 1));
    printf("\n"); 
}

#endif
