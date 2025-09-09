#include <faiss/IndexFlat.h>
#ifdef WITH_GPU
#include <faiss/gpu/GpuIndexFlat.h>
#include <faiss/gpu/StandardGpuResources.h>
#endif

#ifdef WITH_GPU
void dummy_main() {
    faiss::gpu::StandardGpuResources res;
    faiss::gpu::GpuIndexFlatL2 index(&res, 8);
}
#endif

int main() {
    faiss::IndexFlatL2 index(8);
}
