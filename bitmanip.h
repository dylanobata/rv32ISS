#ifndef BITMANIP
#define BITMANIP

#include <stdint.h>

uint8_t get_bit(uint32_t bits, uint8_t position) {
    // position indexed at 0 ending at 31 
    position %= 32; // if position >= 32 wrap around
    bits = bits >> position;
    return bits & 0x1;
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
