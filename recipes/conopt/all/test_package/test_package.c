#include <conopt.h>
#include <stdio.h>

int main() {
    int major, minor, patch;
    COIGET_Version(&major, &minor, &patch);
    printf("CONOPT version %d.%d.%d\n", major, minor, patch);
}
