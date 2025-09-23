find_package(GFlags REQUIRED)
find_package(SQLite3 REQUIRED)
find_package(Eigen3 REQUIRED)
find_package(stdgpu REQUIRED)
find_package(glog REQUIRED)
find_package(CUDAToolkit REQUIRED)

link_libraries(
    Eigen3::Eigen
    stdgpu::stdgpu
    CUDA::nppi
    CUDA::nvtx3
    CUDA::curand
)
