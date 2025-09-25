import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd, stdcpp_library
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class CuoptConan(ConanFile):
    name = "cuopt"
    description = ("NVIDIA cuOpt is a GPU-accelerated optimization engine that excels in mixed integer linear programming (MILP),"
                   " linear programming (LP), and vehicle routing problems (VRP).")
    license = "Apache-2.0"
    homepage = "https://github.com/NVIDIA/cuopt"
    topics = ("optimization", "routing", "gpu", "cuda", "linear-programming")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "logging_level": ["trace", "debug", "info", "warn", "error", "critical", "off"]
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "logging_level": "info",
    }
    implements = ["auto_shared_fpic"]

    python_requires = "conan-cuda/latest"
    python_requires_extend = "conan-cuda.Cuda"

    def export_sources(self):
        copy(self, "conan_deps.cmake", self.recipe_folder, os.path.join(self.export_sources_folder, "src", "cpp"))

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("rmm/[>=25.04]", transitive_headers=True, transitive_libs=True)
        self.requires("raft/[>=25.04]", transitive_headers=True, transitive_libs=True)
        self.requires("rapids_logger/[>=0.1 <1]", transitive_headers=True, transitive_libs=True)
        self.requires("argparse/[^3]")
        self.requires("openmp/system")
        self.cuda.requires("cudart")
        self.cuda.requires("cublas")
        self.cuda.requires("cusparse")
        self.cuda.requires("curand")
        self.cuda.requires("cusolver")
        self.cuda.requires("cuda-profiler-api")
        if Version(self.version) >= "25.10":
            self.requires("onetbb/[*]")

    def validate(self):
        check_min_cppstd(self, 17)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.26.4]")
        self.tool_requires("rapids-cmake/25.08.00")
        self.tool_requires(f"nvcc/[~{self.settings.cuda.version}]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        save(self, "cmake/RAPIDS.cmake", "find_package(rapids-cmake REQUIRED)")
        rm(self, "FindTBB.cmake", "cpp/cmake/thirdparty")
        replace_in_file(self, "cpp/CMakeLists.txt", " -Werror ", " ")
        replace_in_file(self, "cpp/CMakeLists.txt", " -Xcompiler=-Werror", " ")
        replace_in_file(self, "cpp/libmps_parser/CMakeLists.txt", " -Werror ", " ")
        replace_in_file(self, "cpp/CMakeLists.txt", "CXX_STANDARD 17", "")
        replace_in_file(self, "cpp/CMakeLists.txt", "CUDA_STANDARD 17", "")
        replace_in_file(self, "cpp/libmps_parser/CMakeLists.txt", "CXX_STANDARD 17", "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["CMAKE_PROJECT_CUOPT_INCLUDE"] = "conan_deps.cmake"
        tc.cache_variables["LIBCUOPT_LOGGING_LEVEL"] = str(self.options.logging_level).upper()
        tc.cache_variables["BUILD_TESTS"] = False
        tc.cache_variables["BUILD_BENCHMARKS"] = False
        tc.cache_variables["CUOPT_BUILD_TESTUTIL"] = False
        tc.cache_variables["FETCH_RAPIDS"] = False
        tc.cache_variables["FETCHCONTENT_FULLY_DISCONNECTED"] = True
        tc.cache_variables["CMAKE_PREFIX_PATH"] = self.generators_folder.replace("\\", "/")
        tc.cache_variables["CMAKE_DISABLE_FIND_PACKAGE_Doxygen"] = True
        tc.generate()

        deps = CMakeDeps(self)
        deps.build_context_activated.append("rapids-cmake")
        deps.build_context_build_modules.append("rapids-cmake")
        deps.set_property("rmm", "cmake_file_name", "RMM")
        deps.set_property("raft", "cmake_file_name", "RAFT")
        deps.generate()

        cuda_tc = self.cuda.CudaToolchain()
        cuda_tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder="cpp")
        cmake.build()

    def package(self):
        copy(self, "LICENSE*", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "cuopt")
        self.cpp_info.set_property("cmake_additional_variables_prefixes", ["CUOPT", "MPS_PARSER"])

        self.cpp_info.components["cuopt_"].set_property("cmake_target_name", "cuopt::cuopt")
        self.cpp_info.components["cuopt_"].libs = ["cuopt"]
        self.cpp_info.components["cuopt_"].defines = [f"CUOPT_LOG_ACTIVE_LEVEL=RAPIDS_LOGGER_LOG_LEVEL_{str(self.options.logging_level).upper()}"]
        self.cpp_info.components["cuopt_"].requires = [
            "mps_parser",
            "rmm::rmm",
            "raft::raft",
            "rapids_logger::rapids_logger",
            "openmp::openmp",
            "argparse::argparse",
            "cudart::cudart_",
            "cublas::cublas_",
            "cusparse::cusparse",
            "curand::curand",
            "cusolver::cusolver_",
            "cuda-profiler-api::cuda-profiler-api",
        ]
        if Version(self.version) >= "25.10":
            self.cpp_info.components["cuopt_"].requires.append("onetbb::libtbb")

        self.cpp_info.components["mps_parser"].set_property("cmake_target_name", "cuopt::mps_parser")
        self.cpp_info.components["mps_parser"].libs = ["mps_parser"]

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["cuopt_"].system_libs = ["m",]
            self.cpp_info.components["mps_parser"].system_libs = ["m"]
        if not self.options.shared and stdcpp_library(self):
            self.cpp_info.components["cuopt_"].system_libs.append(stdcpp_library(self))
