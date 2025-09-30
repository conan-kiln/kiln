#include <wholememory/wholememory.h>
#include <stdio.h>

int main() {
    printf("cuGRAPH GNN was built with NVSHMEM support: %s\n", wholememory_is_build_with_nvshmem() ? "yes" : "no");
}
