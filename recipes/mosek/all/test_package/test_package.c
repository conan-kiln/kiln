#include <mosek.h>
#include <stdio.h>

int main() {
    int major, minor, revision;
    MSK_getversion(&major, &minor, &revision);
    printf("MOSEK version: %d.%d.%d\n", major, minor, revision);
}
