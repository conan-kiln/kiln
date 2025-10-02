find_package(assimp REQUIRED)
find_package(BLAS REQUIRED)
find_package(cppzmq REQUIRED)
find_package(CURL REQUIRED)
find_package(Eigen3 REQUIRED)
find_package(embree REQUIRED)
find_package(fmt REQUIRED)
find_package(GLEW REQUIRED)
find_package(glfw3 REQUIRED)
find_package(JPEG REQUIRED)
find_package(jsoncpp REQUIRED)
find_package(LAPACK REQUIRED)
find_package(liblzf REQUIRED)
find_package(minizip REQUIRED)
find_package(msgpack-cxx REQUIRED)
find_package(nanoflann REQUIRED)
find_package(OpenGL REQUIRED)
find_package(PNG REQUIRED)
find_package(poissonrecon REQUIRED)
find_package(Qhull REQUIRED)
find_package(rply REQUIRED)
find_package(TBB REQUIRED)
find_package(tinyfiledialogs REQUIRED)
find_package(TinyGLTF REQUIRED)
find_package(tinyobjloader REQUIRED)
find_package(uvatlas REQUIRED)

if(WITH_OPENMP)
  find_package(OpenMP REQUIRED)
  link_libraries(Open3D::3rdparty_openmp)
endif()

set(Open3D_3RDPARTY_PRIVATE_TARGETS
  assimp::assimp
  BLAS::BLAS
  CURL::libcurl
  embree::embree
  GLEW::GLEW
  JPEG::JPEG
  LAPACK::LAPACK
  liblzf::liblzf
  Microsoft::UVAtlas
  minizip::minizip
  Open3D::3rdparty_cppzmq
  Open3D::3rdparty_eigen3
  Open3D::3rdparty_fmt
  Open3D::3rdparty_glfw
  Open3D::3rdparty_jsoncpp
  Open3D::3rdparty_msgpack
  Open3D::3rdparty_nanoflann
  Open3D::3rdparty_poissonrecon
  Open3D::3rdparty_qhull
  Open3D::3rdparty_tinyfiledialogs
  Open3D::3rdparty_tinygltf
  Open3D::3rdparty_vtk
  PNG::PNG
  rply::rply
  tinyobjloader::tinyobjloader
)
include_directories(
  ${CMAKE_SOURCE_DIR}/3rdparty/tomasakeninemoeller/include
)
link_libraries(
  Open3D::3rdparty_eigen3
  Open3D::3rdparty_fmt
)

find_package(VTK REQUIRED)
add_library(3rdparty_vtk INTERFACE)
add_library(Open3D::3rdparty_vtk ALIAS 3rdparty_vtk)
target_link_libraries(3rdparty_vtk INTERFACE
  VTK::FiltersGeneral
  VTK::FiltersSources
  VTK::FiltersModeling
  VTK::FiltersCore
  VTK::CommonExecutionModel
  VTK::CommonDataModel
  VTK::CommonTransforms
  VTK::CommonMath
  VTK::CommonMisc
  VTK::CommonSystem
  VTK::CommonCore
  VTK::kissfft
  VTK::pugixml
  VTK::vtksys
)

if(BUILD_GUI)
  find_package(filament REQUIRED)
  find_package(imgui REQUIRED)
  link_libraries(
    filament::filament
    imgui::imgui
  )
endif()

if(BUILD_CUDA_MODULE)
  find_package(CUDAToolkit REQUIRED)
  find_package(NvidiaCutlass REQUIRED)
  find_package(stdgpu REQUIRED)
  link_libraries(
    Open3D::3rdparty_cutlass
    CUDA::cudart
    CUDA::cublas
    CUDA::cusolver
    stdgpu::stdgpu
  )
endif()
