#include <rerun/c/rerun.h>
#include <stdio.h>

int main() {
    printf("Rerun C API version: %s\n", rr_version_string());
}
