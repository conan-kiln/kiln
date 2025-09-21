import os
from functools import cached_property
from pathlib import Path

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class TinyCudaNnConan(ConanFile):
    name = "tiny-cuda-nn"
    description = "Lightning fast & tiny C++/CUDA neural network framework"
    license = "BSD-3-Clause"
    homepage = "https://github.com/NVlabs/tiny-cuda-nn"
    topics = ("neural-networks", "cuda", "machine-learning", "deep-learning")
    package_type = "static-library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "fPIC": [True, False],
        "with_cusolver": [True, False],
        "with_nvrtc": [True, False],
    }
    default_options = {
        "fPIC": True,
        "with_cusolver": False,
        "with_nvrtc": False,
    }
    implements = ["auto_shared_fpic"]

    python_requires = "conan-cuda/latest"

    @cached_property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self)

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("fmt/[*]", transitive_headers=True, transitive_libs=True)
        self.requires("cutlass/[^4]", transitive_headers=True, transitive_libs=True)
        self.requires("nlohmann_json/[^3]", transitive_headers=True, transitive_libs=True)
        self.cuda.requires("cudart", transitive_headers=True, transitive_libs=True)
        if self.options.with_cusolver:
            self.cuda.requires("cusolver", transitive_headers=True, transitive_libs=True)
        if self.options.with_nvrtc:
            self.cuda.requires("nvrtc", transitive_headers=True, transitive_libs=True)

    def validate(self):
        check_min_cppstd(self, 14)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.18]")
        self.tool_requires("cmrc/[*]")
        self.tool_requires(f"nvcc/[~{self.settings.cuda.version}]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        for path in Path("dependencies").iterdir():
            if path.name != "pcg32":
                rmdir(self, path)
        replace_in_file(self, "CMakeLists.txt",
                        'string(REPLACE "-virtual" "" MIN_GPU_ARCH "${MIN_GPU_ARCH}")',
                        'string(REPLACE "-virtual" "" MIN_GPU_ARCH "${MIN_GPU_ARCH}")\n'
                        'string(REPLACE "-real" "" MIN_GPU_ARCH "${MIN_GPU_ARCH}")')

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["TCNN_BUILD_EXAMPLES"] = False
        tc.cache_variables["TCNN_BUILD_BENCHMARK"] = False
        tc.cache_variables["TCNN_BUILD_TESTS"] = False
        tc.cache_variables["TCNN_EXTERNAL_FMT"] = True
        tc.cache_variables["TCNN_ALLOW_CUBLAS_CUSOLVER"] = self.options.with_cusolver
        tc.cache_variables["TCNN_BUILD_WITH_RTC"] = self.options.with_nvrtc
        tc.cache_variables["TCNN_CUDA_ARCHITECTURES"] = str(self.settings.cuda.architectures).replace(",", ";")
        tc.cache_variables["CMAKE_TRY_COMPILE_CONFIGURATION"] = str(self.settings.build_type)
        tc.generate()

        deps = CMakeDeps(self)
        deps.build_context_activated.append("cmrc")
        deps.build_context_build_modules.append("cmrc")
        deps.generate()

        cuda_tc = self.cuda.CudaToolchain()
        cuda_tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "LICENSE.txt", os.path.join(self.source_folder, "dependencies"), os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        copy(self, "*.h", os.path.join(self.source_folder, "dependencies"), os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.libs = ["tiny-cuda-nn"]
        self.cpp_info.defines = ["TCNN_CMRC"]
        architectures = [x.split("-")[0] for x in str(self.settings.cuda.architectures).split(",")]
        min_arch = min(int(x) for x in architectures if x.isnumeric())
        if min_arch:
            self.cpp_info.defines.append(f"TCNN_MIN_GPU_ARCH={min_arch}")
