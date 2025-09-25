import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class CuGraphGnnConan(ConanFile):
    name = "cugraph-gnn"
    description = "cuGraph GNN supports the creation and manipulation of graphs followed by the execution of scalable fast graph algorithms"
    license = "Apache-2.0"
    homepage = "https://github.com/rapidsai/cugraph-gnn"
    topics = ("gpu", "graph", "analytics", "cuda", "distributed-computing", "wholegraph", "rapids")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_nvshmem": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_nvshmem": False,
    }
    implements = ["auto_shared_fpic"]

    python_requires = "conan-cuda/latest", "conan-utils/latest"
    python_requires_extend = "conan-cuda.Cuda"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.cuda.requires("cudart", transitive_headers=True, transitive_libs=True)
        self.cuda.requires("nvml-stubs")
        self.requires("nccl/[^2]")
        self.requires("raft/[*]")
        if self.options.with_nvshmem:
            self.requires("nvshmem/[^3]", options={"internal_headers": True})

    def validate(self):
        check_min_cppstd(self, 17)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.30.4]")
        self.tool_requires("rapids-cmake/25.08.00")
        self.cuda.tool_requires("nvcc")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        save(self, "cmake/RAPIDS.cmake", "find_package(rapids-cmake REQUIRED)")
        save(self, "cpp/cmake/thirdparty/get_raft.cmake", "find_package(raft REQUIRED)")
        save(self, "cpp/cmake/thirdparty/get_nccl.cmake", "find_package(nccl REQUIRED)")
        save(self, "cpp/cmake/thirdparty/get_nvshmem.cmake",
             "find_package(NVSHMEM REQUIRED)\n"
             "include_directories(${NVSHMEM_INCLUDE_DIR}/internal/bootstrap_host)")
        replace_in_file(self, "cpp/CMakeLists.txt", "get_target_property(NVSHMEM_BINARY_DIR nvshmem BINARY_DIR)", "")
        replace_in_file(self, "cpp/CMakeLists.txt", "list(APPEND WHOLEGRAPH_INSTALL_LIBS nvshmem", "# ")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_SHARED_LIBS"] = self.options.shared
        tc.cache_variables["BUILD_TESTS"] = False
        tc.cache_variables["BUILD_BENCHMARKS"] = False
        tc.cache_variables["FETCH_RAPIDS"] = False
        tc.cache_variables["FETCHCONTENT_FULLY_DISCONNECTED"] = True
        tc.cache_variables["CMAKE_PREFIX_PATH"] = self.generators_folder.replace("\\", "/")
        tc.cache_variables["CMAKE_DISABLE_FIND_PACKAGE_Doxygen"] = True
        tc.cache_variables["BUILD_WITH_NVSHMEM"] = self.options.with_nvshmem
        if self.options.with_nvshmem:
            tc.cache_variables["NVSHMEM_BINARY_DIR"] = self.dependencies["nvshmem"].package_folder.replace("\\", "/")
        tc.generate()

        deps = CMakeDeps(self)
        deps.build_context_activated.append("rapids-cmake")
        deps.build_context_build_modules.append("rapids-cmake")
        deps.set_property("nccl", "cmake_target_name", "NCCL::NCCL")
        deps.generate()

        cuda_tc = self.cuda.CudaToolchain()
        cuda_tc.extra_cudaflags.append("--expt-relaxed-constexpr")
        cuda_tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder="cpp")
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "wholegraph")

        self.cpp_info.components["wholegraph"].set_property("cmake_target_name", "wholegraph::wholegraph")
        self.cpp_info.components["wholegraph"].libs = ["wholegraph"]
        self.cpp_info.components["wholegraph"].requires = ["raft::raft", "cudart::cudart_", "nvml-stubs::nvml-stubs", "nccl::nccl"]

        if self.options.with_nvshmem:
            self.cpp_info.components["nvshmem_wholememory_bootstrap"].set_property("cmake_target_name", "wholegraph::nvshmem_wholememory_bootstrap")
            self.cpp_info.components["nvshmem_wholememory_bootstrap"].libs = ["nvshmem_wholememory_bootstrap"]
            self.cpp_info.components["nvshmem_wholememory_bootstrap"].requires = ["wholegraph", "nvshmem::nvshmem_host"]
            self.cpp_info.components["wholegraph"].requires.extend(["nvshmem::nvshmem_host", "nvshmem::nvshmem_device"])
