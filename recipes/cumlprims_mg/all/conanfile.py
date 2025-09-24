import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class CumlprimsMgConan(ConanFile):
    name = "cumlprims_mg"
    description = "Multi-node multi-GPU (MNMG) ML mathematical primitives and algorithms"
    license = "Apache-2.0"
    homepage = "https://github.com/rapidsai/cumlprims_mg"
    topics = ("machine-learning", "gpu", "cuda", "rapids", "multi-gpu")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_nvtx": [True, False],
        "with_openmp": [True, False],
    }
    default_options = {
        "shared": True,
        "fPIC": True,
        "with_nvtx": False,
        "with_openmp": True,
    }
    implements = ["auto_shared_fpic"]

    python_requires = "conan-cuda/latest"
    python_requires_extend = "conan-cuda.Cuda"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("raft/[*]", transitive_headers=True)
        self.requires("rmm/[*]")
        self.cuda.requires("cudart")
        self.cuda.requires("cublas")
        self.cuda.requires("curand")
        self.cuda.requires("cusolver")
        self.cuda.requires("cusparse")
        if self.options.with_nvtx:
            self.requires("nvtx/[^3]")
        if self.options.with_openmp:
            self.requires("openmp/system")

    def validate(self):
        check_min_cppstd(self, 17)
        if self.cuda.major < 12:
            raise ConanInvalidConfiguration("cumlprims_mg requires CUDA >= 12.0")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.30.4]")
        self.tool_requires("rapids-cmake/[*]")
        self.tool_requires(f"nvcc/[~{self.settings.cuda.version}]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        save(self, "cmake/RAPIDS.cmake", "find_package(rapids-cmake REQUIRED)")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_TESTS"] = False
        tc.cache_variables["BUILD_CUMLPRIMS_LIBRARY"] = True
        tc.cache_variables["DISABLE_OPENMP"] = not self.options.with_openmp
        tc.cache_variables["NVTX"] = self.options.with_nvtx
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
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "cumlprims_mg")
        self.cpp_info.set_property("cmake_target_name", "cumlprims_mg::cumlprims_mg")
        self.cpp_info.libs = ["cumlprims_mg"]
        self.cpp_info.requires = [
            "raft::raft",
            "rmm::rmm",
            "cudart::cudart_",
            "cublas::cublas_",
            "curand::curand",
            "cusolver::cusolver_",
            "cusparse::cusparse",
        ]
        if self.options.with_nvtx:
            self.cpp_info.requires.append("nvtx::nvtx")
        if self.options.with_openmp:
            self.cpp_info.requires.append("openmp::openmp")
        if self.settings.os in ["Linux", "FreeBSD"]:
            if self.options.with_openmp:
                self.cpp_info.system_libs  = ["m", "pthread"]
