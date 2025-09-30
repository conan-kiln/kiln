#include <vl/sift.h>
#include <stdio.h>

int main() {
#ifdef VL_STATIC
    vl_constructor();
#endif
    VL_PRINT("Hello World! This is VLFeat.\n");
    VlSiftFilt *sift = vl_sift_new(16, 16, 1, 3, 0);
    if (!sift) {
        printf("Failed to initialize SIFT descriptor.\n");
        return 1;
    }
    vl_sift_delete(sift);
}
