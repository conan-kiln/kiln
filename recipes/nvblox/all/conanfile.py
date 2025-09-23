import os
from functools import cached_property

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class NvbloxConan(ConanFile):
    name = "nvblox"
    description = "GPU-accelerated library for volumetric mapping using Signed Distance Fields"
    license = "Apache-2.0"
    homepage = "https://github.com/NVIDIA-ISAAC-ROS/nvblox"
    topics = ("robotics", "mapping", "cuda", "sdf", "gpu")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type", "cuda"

    python_requires = "conan-cuda/latest"

    @cached_property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self)

    def export_sources(self):
        export_conandata_patches(self)
        copy(self, "conan_deps.cmake", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        # Thrust 2.3.0 no longer supports deprecated thrust::pair, which nvblox still relies on
        self.requires("cuda-cccl/[<2.3.0]", transitive_headers=True, transitive_libs=True)
        self.cuda.requires("cudart", transitive_headers=True, transitive_libs=True)
        self.cuda.requires("npp", transitive_headers=True, transitive_libs=True)
        self.cuda.requires("nvtx", transitive_headers=True)
        self.cuda.requires("curand", transitive_headers=True)
        self.requires("stdgpu/1.3.0-nvblox.20240211", transitive_headers=True, transitive_libs=True, options={"backend": "cuda"})
        self.requires("eigen/3.4.0", transitive_headers=True)
        self.requires("gflags/[^2]", transitive_headers=True, transitive_libs=True)
        self.requires("glog/[>=0.5 <1]", transitive_headers=True, transitive_libs=True)
        self.requires("sqlite3/[^3]")

    def validate(self):
        check_min_cppstd(self, 17)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.22]")
        self.tool_requires(f"nvcc/[~{self.settings.cuda.version}]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        save(self, "nvblox/examples/CMakeLists.txt", "")
        replace_in_file(self, "nvblox/CMakeLists.txt", "add_nvblox_executable(", "message(TRACE # add_nvblox_executable(")
        replace_in_file(self, "cmake/nvblox_targets.cmake", 'add_host_compiler_option(${target_name} "-std=gnu++17")', "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["CMAKE_PROJECT_nvblox_INCLUDE"] = "conan_deps.cmake"
        tc.cache_variables["PRE_CXX11_ABI_LINKABLE"] = self.settings.get_safe("compiler.libcxx") == "libstdc++"
        tc.cache_variables["BUILD_PYTORCH_WRAPPER"] = False
        tc.cache_variables["BUILD_TESTING"] = False
        tc.cache_variables["BUILD_EXPERIMENTS"] = False
        tc.cache_variables["WARNING_AS_ERROR"] = False
        tc.cache_variables["CMAKE_CUDA_ARCHITECTURES"] = self.settings.cuda.architectures.value.replace(",", ";")
        tc.cache_variables["FETCHCONTENT_FULLY_DISCONNECTED"] = True
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("eigen", "cmake_target_aliases", ["nvblox_eigen"])
        deps.set_property("stdgpu", "cmake_target_aliases", ["nvblox_stdgpu"])
        deps.generate()

        cuda_tc = self.cuda.CudaToolchain()
        cuda_tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE.md", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "nvblox")

        self.cpp_info.components["nvblox_lib"].set_property("cmake_target_name", "nvblox::nvblox_lib")
        self.cpp_info.components["nvblox_lib"].libs = ["nvblox_lib"]
        self.cpp_info.components["nvblox_lib"].includedirs.append("include/nvblox")
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["nvblox_lib"].system_libs = ["m"]
        self.cpp_info.components["nvblox_lib"].requires = [
            "cuda-cccl::cuda-cccl",
            "cudart::cudart_",
            "npp::nppi",
            "nvtx::nvtx",
            "curand::curand",
            "stdgpu::stdgpu",
            "glog::glog",
            "gflags::gflags",
            "eigen::eigen",
            "sqlite3::sqlite3",
        ]

        self.cpp_info.components["nvblox_datasets"].set_property("cmake_target_name", "nvblox::nvblox_datasets")
        self.cpp_info.components["nvblox_datasets"].libs = ["nvblox_datasets"]
        self.cpp_info.components["nvblox_datasets"].requires = ["nvblox_lib"]
