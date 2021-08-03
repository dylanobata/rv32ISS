#ifndef BITMANIP
#define BITMANIP

#include <stdint.h>

int32_t get_bits(uint8_t n, uint8_t position ,uint32_t bits) {
    return (((1 << n) - 1) & (bits >> (position - 1)));
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
