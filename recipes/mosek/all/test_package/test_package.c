#include <mosek.h>
#include <stdio.h>

int main() {
#if MSK_VERSION_MAJOR >= 9
    int major, minor, revision;
    MSK_getversion(&major, &minor, &revision);
    printf("MOSEK version: %d.%d.%d\n", major, minor, revision);
#else
    int major, minor, build, revision;
    MSK_getversion(&major, &minor, &build, &revision);
    printf("MOSEK version: %d.%d.%d.%d\n", major, minor, build, revision);
#endif
}
