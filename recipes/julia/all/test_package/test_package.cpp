#include <julia/julia.h>
#include <stdio.h>

int main() {
    jl_box_uint8(255);
    printf("Julia version: %s\n", JULIA_VERSION_STRING);
}
