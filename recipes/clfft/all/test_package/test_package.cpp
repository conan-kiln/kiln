#include <clFFT.h>
#include <stdio.h>

int main() {
    cl_uint major, minor, patch;
    clfftGetVersion(&major,&minor,&patch);
    printf("clFFT version %d.%d.%d\n", major, minor, patch);
}
