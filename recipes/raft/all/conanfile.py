import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class RaftConan(ConanFile):
    name = "raft"
    description = "RAFT: Reusable Accelerated Functions and Tools for data science and machine learning"
    license = "Apache-2.0"
    homepage = "https://github.com/rapidsai/raft"
    topics = ("cuda", "gpu", "machine-learning", "data-science", "linear-algebra")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "header_only": [True, False],
        "shared": [True, False],
        "fPIC": [True, False],
        "distributed": [True, False],
        "with_nvtx": [True, False],
        "with_openmp": [True, False],
    }
    default_options = {
        "header_only": True,
        "shared": False,
        "fPIC": True,
        "distributed": False,
        "with_nvtx": True,
        "with_openmp": True,
    }
    implements = ["auto_shared_fpic", "auto_header_only"]
    python_requires = "conan-cuda/latest"

    @property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("rmm/[*]", transitive_headers=True, transitive_libs=True)
        self.requires("rapids_logger/[>=0.1 <1]", transitive_headers=True)
        self.requires("cutlass/[^3]", transitive_headers=True)
        self.cuda.requires("cucollections", transitive_headers=True)
        self.cuda.requires("cusolver", transitive_headers=True, transitive_libs=True)
        self.cuda.requires("cusparse", transitive_headers=True, transitive_libs=True)
        self.cuda.requires("cublas", transitive_headers=True, transitive_libs=True)
        self.cuda.requires("curand", transitive_headers=True, transitive_libs=True)
        if self.options.with_openmp:
            self.requires("openmp/system", transitive_headers=True, transitive_libs=True)
        if self.options.with_nvtx:
            self.cuda.requires("nvtx", transitive_headers=True)
        if self.options.distributed:
            self.requires("nccl/[^2]", transitive_headers=True, transitive_libs=True)
            self.requires("ucxx/[>=0.44 <1]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        check_min_cppstd(self, 17)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.30.4]")
        self.tool_requires("rapids-cmake/25.08.00")
        self.tool_requires(f"nvcc/[~{self.settings.cuda.version}]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        save(self, "cmake/RAPIDS.cmake", "find_package(rapids-cmake REQUIRED)")
        save(self, "cpp/cmake/thirdparty/get_cccl.cmake", "find_package(CUDAToolkit REQUIRED)")
        save(self, "cpp/cmake/thirdparty/get_rmm.cmake", "find_package(rmm REQUIRED)")
        save(self, "cpp/cmake/thirdparty/get_cutlass.cmake", "find_package(NvidiaCutlass REQUIRED)")
        replace_in_file(self, "cpp/CMakeLists.txt", "rapids_cpm_cuco(", "find_package(cuco REQUIRED) #")
        # Don't fail if OpenMP::OpenMP_CUDA is not found
        replace_in_file(self, "cpp/CMakeLists.txt", "OpenMP REQUIRED", "OpenMP REQUIRED CXX")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["RAFT_COMPILE_LIBRARY"] = not self.options.header_only
        tc.cache_variables["RAFT_COMPILE_DYNAMIC_ONLY"] = self.options.get_safe("shared", False)
        tc.cache_variables["RAFT_NVTX"] = self.options.with_nvtx
        tc.cache_variables["DISABLE_OPENMP"] = not self.options.with_openmp
        tc.cache_variables["BUILD_TESTS"] = False
        tc.cache_variables["BUILD_PRIMS_BENCH"] = False
        tc.cache_variables["DETECT_CONDA_ENV"] = False
        tc.cache_variables["FETCHCONTENT_FULLY_DISCONNECTED"] = True
        tc.cache_variables["CMAKE_PREFIX_PATH"] = self.generators_folder.replace("\\", "/")
        tc.generate()

        deps = CMakeDeps(self)
        deps.build_context_activated.append("rapids-cmake")
        deps.build_context_build_modules.append("rapids-cmake")
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
        if not self.options.get_safe("shared"):
            rm(self, "*.so", os.path.join(self.package_folder, "lib"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "raft")

        self.cpp_info.components["raft"].set_property("cmake_target_name", "raft::raft")
        self.cpp_info.components["raft"].libdirs = []
        self.cpp_info.components["raft"].defines = [
            "RAFT_LOG_ACTIVE_LEVEL=RAPIDS_LOGGER_LOG_LEVEL_INFO",
            "RAFT_SYSTEM_LITTLE_ENDIAN=1",
        ]
        # self.cpp_info.components["raft"].cudaflags = ["--expt-extended-lambda", "--expt-relaxed-constexpr"]
        self.cpp_info.components["raft"].requires = [
            "rmm::rmm",
            "cutlass::cutlass",
            "cucollections::cucollections",
            "rapids_logger::rapids_logger",
            "cublas::cublas_",
            "cusolver::cusolver_",
            "cusparse::cusparse",
            "curand::curand",
        ]
        if self.options.with_openmp:
            self.cpp_info.components["raft"].requires.append("openmp::openmp")
        if self.options.with_nvtx:
            self.cpp_info.components["raft"].requires.append("nvtx::nvtx")
            self.cpp_info.components["raft"].defines.append("NVTX_ENABLED")
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["raft"].system_libs = ["m", "pthread", "dl"]

        if not self.options.header_only:
            self.cpp_info.components["compiled"].set_property("cmake_target_name", "raft::raft_lib")
            self.cpp_info.components["compiled"].set_property("cmake_target_aliases", ["raft::compiled", "raft::compiled_static"])
            self.cpp_info.components["compiled"].libs = ["raft"]
            self.cpp_info.components["compiled"].defines = ["RAFT_COMPILED"]
            self.cpp_info.components["compiled"].requires = ["raft"]

        if self.options.distributed:
            self.cpp_info.components["distributed"].set_property("cmake_target_name", "raft::distributed")
            self.cpp_info.components["distributed"].requires = ["raft", "nccl::nccl", "ucxx::ucxx"]
            self.cpp_info.components["distributed"].libdirs = []
