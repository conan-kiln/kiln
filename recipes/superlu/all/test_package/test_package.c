#include <slu_ddefs.h>
#include <stdio.h>

int main() {
    doubleMalloc(10);
    printf("SuperLU version: %d.%d.%d\n", SUPERLU_MAJOR_VERSION, SUPERLU_MINOR_VERSION, SUPERLU_PATCH_VERSION);
}
