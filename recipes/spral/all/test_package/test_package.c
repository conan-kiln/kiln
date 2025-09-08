#include <spral.h>
#include <stdio.h>

int main() {
    char version[11];
    get_spral_version(version);
    printf("SPRAL version: %s\n", version);
}
