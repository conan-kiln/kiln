#include <asl/asl.h>
#include <asl2/asl.h>
#include <stdio.h>

int main() {
    ASL_alloc(1);
    printf("ASL date: %ld\n", ASLdate_ASL);
}
