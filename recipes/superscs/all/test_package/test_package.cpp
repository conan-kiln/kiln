#include <superscs/scs.h>
#include <stdio.h>

int main() {
    ScsSolution *sol = scs_init_sol();
    printf("SuperSCS version: %s\n", SCS_VERSION);
}
