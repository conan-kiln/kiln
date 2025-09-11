#include <conopt.hpp>
#include <stdio.h>

int main() {
    auto version = Conopt::version();
    printf("CONOPT version %d.%d.%d\n", version[0], version[1], version[2]);
}
