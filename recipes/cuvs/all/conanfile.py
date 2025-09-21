import os
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd, stdcpp_library
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class CuVsConan(ConanFile):
    name = "cuvs"
    description = "cuVS: Vector Search and Clustering on the GPU"
    license = "Apache-2.0"
    homepage = "https://github.com/rapidsai/cuvs"
    topics = ("cuda", "vector-search", "nearest-neighbor", "gpu", "machine-learning")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "c_api": [True, False],
        "multi_gpu": [True, False],
        "with_hnswlib": [True, False],
        "with_nvtx": [True, False],
        "with_openmp": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "c_api": True,
        "multi_gpu": False,
        "with_hnswlib": True,
        "with_nvtx": True,
        "with_openmp": True,
    }
    implements = ["auto_shared_fpic", "auto_header_only"]
    python_requires = "conan-cuda/latest"

    @cached_property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("cutlass/[>=3 <5]", transitive_headers=True, transitive_libs=True)
        self.requires("raft/[>=25.08]", transitive_headers=True, transitive_libs=True)
        self.requires("dlpack/[>=0.8 <1]", transitive_headers=True)
        if self.options.with_hnswlib:
            self.requires("hnswlib/0.8.0-cuvs", transitive_headers=True)
        if self.options.multi_gpu:
            self.requires("nccl/[^2]", transitive_headers=True, transitive_libs=True)
        if self.options.with_nvtx:
            self.cuda.requires("nvtx", transitive_headers=True)
        if self.options.with_openmp:
            self.requires("openmp/system", transitive_headers=True, transitive_libs=True)

    def validate(self):
        check_min_cppstd(self, 17)
        if self.options.multi_gpu and not self.options.shared:
            raise ConanInvalidConfiguration("Multi-GPU algorithms require shared libraries")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.30.4]")
        self.tool_requires("rapids-cmake/25.08.00")
        self.tool_requires(f"nvcc/[~{self.settings.cuda.version}]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # Patch vendored dependencies to use Conan packages
        save(self, "cmake/RAPIDS.cmake", "find_package(rapids-cmake REQUIRED)")
        save(self, "cpp/cmake/thirdparty/get_cutlass.cmake", "find_package(NvidiaCutlass REQUIRED)")
        save(self, "cpp/cmake/thirdparty/get_dlpack.cmake", "find_package(dlpack REQUIRED)\nset(DLPACK_INCLUDE_DIR ${dlpack_INCLUDE_DIR})")
        save(self, "cpp/cmake/thirdparty/get_diskann.cmake", "find_package(diskann REQUIRED)")
        save(self, "cpp/cmake/thirdparty/get_hnswlib.cmake", "find_package(hnswlib REQUIRED)")
        save(self, "cpp/cmake/thirdparty/get_raft.cmake", "find_package(raft REQUIRED)")
        save(self, "cpp/cmake/thirdparty/get_rmm.cmake", "find_package(rmm REQUIRED)")
        # Don't fail if OpenMP::OpenMP_CUDA is not found
        replace_in_file(self, "cpp/CMakeLists.txt", "OpenMP REQUIRED", "OpenMP REQUIRED CXX")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_TESTS"] = False
        tc.cache_variables["BUILD_CUVS_BENCH"] = False
        tc.cache_variables["BUILD_C_LIBRARY"] = self.options.c_api
        tc.cache_variables["BUILD_CAGRA_HNSWLIB"] = self.options.with_hnswlib
        tc.cache_variables["BUILD_MG_ALGOS"] = self.options.multi_gpu
        tc.cache_variables["CUVS_NVTX"] = self.options.with_nvtx
        tc.cache_variables["DISABLE_OPENMP"] = not self.options.with_openmp
        tc.cache_variables["CUVS_COMPILE_DYNAMIC_ONLY"] = self.options.shared
        tc.cache_variables["DETECT_CONDA_ENV"] = False
        tc.cache_variables["FETCHCONTENT_FULLY_DISCONNECTED"] = True
        tc.cache_variables["CMAKE_PREFIX_PATH"] = self.generators_folder.replace("\\", "/")
        # avoid conflicts between RAFT and cuVS both trying to set the cutlass namespace
        tc.preprocessor_definitions["CUTLASS_NAMESPACE"] = "1"
        tc.preprocessor_definitions["cutlass"] = "cuvs_cutlass"
        tc.generate()

        deps = CMakeDeps(self)
        deps.build_context_activated.append("rapids-cmake")
        deps.build_context_build_modules.append("rapids-cmake")
        deps.set_property("nccl", "cmake_target_name", "NCCL::NCCL")
        deps.generate()

        cuda_tc = self.cuda.CudaToolchain()
        cuda_tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder="cpp")
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        if not self.options.shared:
            if self.settings.os == "Windows":
                rm(self, "cuvs.dll", os.path.join(self.package_folder, "bin"))
                rm(self, "cuvs.lib", os.path.join(self.package_folder, "lib"))
            else:
                rm(self, "*.so", os.path.join(self.package_folder, "lib"))
                rm(self, "*.dylib", os.path.join(self.package_folder, "lib"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "cuvs")

        self.cpp_info.components["cuvs_"].set_property("cmake_target_name", "cuvs::cuvs")
        self.cpp_info.components["cuvs_"].libs = ["cuvs" if self.options.shared else "cuvs_static"]
        # self.cpp_info.components["cuvs_"].cudaflags = ["--expt-extended-lambda", "--expt-relaxed-constexpr"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["cuvs_"].system_libs = ["m", "pthread", "dl"]
        self.cpp_info.components["cuvs_"].requires = ["cutlass::cutlass", "raft::raft", "dlpack::dlpack"]
        if self.options.with_hnswlib:
            self.cpp_info.components["cuvs_"].requires.append("hnswlib::hnswlib")
            self.cpp_info.components["cuvs_"].defines.append("CUVS_BUILD_CAGRA_HNSWLIB")
        if self.options.multi_gpu:
            self.cpp_info.components["cuvs_"].requires.append("nccl::nccl")
            self.cpp_info.components["cuvs_"].defines.append("CUVS_BUILD_MG_ALGOS")
        if self.options.with_nvtx:
            self.cpp_info.components["cuvs_"].requires.append("nvtx::nvtx")
            self.cpp_info.components["cuvs_"].defines.append("NVTX_ENABLED")
        if self.options.with_openmp:
            self.cpp_info.components["cuvs_"].requires.append("openmp::openmp")

        if self.options.c_api:
            self.cpp_info.components["c_api"].set_property("cmake_target_name", "cuvs::c_api")
            self.cpp_info.components["c_api"].libs = ["cuvs_c"]
            self.cpp_info.components["c_api"].requires = ["cuvs_"]
            if not self.options.shared and stdcpp_library(self):
                self.cpp_info.components["c_api"].system_libs.append(stdcpp_library(self))
