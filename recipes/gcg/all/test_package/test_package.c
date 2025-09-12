#include <gcg/gcg_general.h>
#include <stdio.h>

int main() {
    printf("GCG version: %d.%d.%d.%d\n", GCGmajorVersion(), GCGminorVersion(), GCGtechVersion(), GCGsubversion());
}
