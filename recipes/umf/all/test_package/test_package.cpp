#include <umf.h>
#include <umf/pools/pool_scalable.h>
#include <umf/providers/provider_os_memory.h>
#include <stdio.h>

int main() {
    printf("UMF version: %d\n", umfGetCurrentVersion());
    umf_result_t res;
    const umf_memory_provider_ops_t *provider_ops = umfOsMemoryProviderOps();
    umf_os_memory_provider_params_handle_t params = NULL;
    umf_memory_provider_handle_t provider;
    res = umfOsMemoryProviderParamsCreate(&params);
    if (res != UMF_RESULT_SUCCESS) {
        printf("Failed to create OS memory provider params!\n");
        return -1;
    }
}
