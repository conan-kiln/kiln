#include <matx.h>
#include <matx/version_config.h>
#include <cstdio>

int main() {
    matx::make_tensor<float>({100});
    printf("MatX version: %d.%d.%d\n", MATX_VERSION_MAJOR, MATX_VERSION_MINOR, MATX_VERSION_PATCH);
}
