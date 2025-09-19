#include <clSPARSE.h>
#include <stdio.h>

int main() {
    cl_uint major, minor, patch, tweak;
    clsparseGetVersion(&major, &minor, &patch, &tweak);
    printf("clSPARSE version %d.%d.%d.%d\n", major, minor, patch, tweak);
}
