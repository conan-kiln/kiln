#include <oapv.h>
#include <stdio.h>

int main() {
    int version;
    printf("openapv version: %s\n", oapv_version(&version));
}
