import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd, stdcpp_library
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class CuGraphConan(ConanFile):
    name = "cugraph"
    description = "cuGraph: RAPIDS Graph Analytics Library"
    license = "Apache-2.0"
    homepage = "https://github.com/rapidsai/cugraph"
    topics = ("gpu", "graph", "analytics", "cuda", "rapids")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }
    implements = ["auto_shared_fpic"]

    python_requires = "conan-cuda/latest", "conan-utils/latest"
    python_requires_extend = "conan-cuda.Cuda"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def export_sources(self):
        copy(self, "conan_deps.cmake", self.recipe_folder, os.path.join(self.export_sources_folder, "src", "cpp"))

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.cuda.requires("cucollections", transitive_headers=True, transitive_libs=True)
        self.cuda.requires("cudart", transitive_headers=True, transitive_libs=True)
        self.requires("rmm/[*]", transitive_headers=True, transitive_libs=True)
        self.requires("raft/[*]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        check_min_cppstd(self, 17)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.30.4]")
        self.tool_requires("rapids-cmake/25.08.00")
        self.cuda.tool_requires("nvcc")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        save(self, "cmake/RAPIDS.cmake", "find_package(rapids-cmake REQUIRED)")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["CMAKE_PROJECT_CUGRAPH_INCLUDE"] = "conan_deps.cmake"
        tc.cache_variables["BUILD_SHARED_LIBS"] = self.options.shared
        tc.cache_variables["BUILD_TESTS"] = False
        tc.cache_variables["BUILD_BENCHMARKS"] = False
        tc.cache_variables["FETCH_RAPIDS"] = False
        tc.cache_variables["FETCHCONTENT_FULLY_DISCONNECTED"] = True
        tc.cache_variables["CMAKE_PREFIX_PATH"] = self.generators_folder.replace("\\", "/")
        tc.cache_variables["CMAKE_DISABLE_FIND_PACKAGE_Doxygen"] = True
        tc.cache_variables["BUILD_CUGRAPH_MG_TESTS"] = False
        tc.cache_variables["CUGRAPH_COMPILE_RAFT_LIB"] = False
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
        self._utils.limit_build_jobs(self, gb_mem_per_job=1.8)
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "cugraph")

        self.cpp_info.components["cugraph_"].set_property("cmake_target_name", "cugraph::cugraph")
        self.cpp_info.components["cugraph_"].libs = ["cugraph"]
        self.cpp_info.components["cugraph_"].requires = ["rmm::rmm", "raft::raft", "cucollections::cucollections", "cudart::cudart_"]
        self.cpp_info.components["cugraph_"].defines = ["CUDA_API_PER_THREAD_DEFAULT_STREAM"]

        self.cpp_info.components["cugraph_c"].set_property("cmake_target_name", "cugraph::cugraph_c")
        self.cpp_info.components["cugraph_c"].libs = ["cugraph_c"]
        self.cpp_info.components["cugraph_c"].requires = ["cugraph_"]
        if not self.options.shared and stdcpp_library(self):
            self.cpp_info.components["cugraph_c"].system_libs.append(stdcpp_library(self))
