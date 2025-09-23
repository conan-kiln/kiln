#include <knitro.h>
#include <stdio.h>

int main() {
    char release[1000];
    KN_get_release(sizeof(release), release);
    puts(release);
}
