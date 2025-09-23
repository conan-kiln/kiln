#include <clBLAS.h>
#include <stdio.h>

int main() {
    cl_uint major, minor, patch;
    clblasGetVersion(&major,&minor,&patch);
    printf("clBLAS version %d.%d.%d\n", major,minor,patch);
}
