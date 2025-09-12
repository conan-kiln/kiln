#include <superlu_mt/slu_mt_ddefs.h>
#include <superlu_mt/slu_mt_util.h>
#include <stdio.h>

int main() {
    intMalloc(10);
    printf("SuperLU_MT version: %d.%d.%d\n", SUPERLU_MT_MAJOR_VERSION, SUPERLU_MT_MINOR_VERSION, SUPERLU_MT_PATCH_VERSION);
}
