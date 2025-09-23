import os
import textwrap
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class MatXConan(ConanFile):
    name = "matx"
    description = "MatX: GPU-accelerated numerical computing in modern C++"
    license = "BSD-3-Clause"
    homepage = "https://github.com/NVIDIA/MatX"
    topics = ("gpu", "cuda", "numerical-computing", "linear-algebra", "tensor", "numpy")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "blas": ["blis", "openblas", "nvpl"],
        "complex_op_nan_checks": [True, False],
        "disable_cub_cache": [True, False],
        "with_cudss": [True, False],
        "with_cutensor": [True, False],
        "with_fftw": [True, False],
        "with_nvtiff": [True, False],
        "with_nvtx": [True, False],
        "with_openmp": [True, False],
    }
    default_options = {
        "blas": "openblas",
        "complex_op_nan_checks": False,
        "disable_cub_cache": False,
        "with_cudss": True,
        "with_cutensor": False,
        "with_fftw": True,
        "with_nvtiff": False,
        "with_nvtx": True,
        "with_openmp": True,
    }

    python_requires = "conan-cuda/latest"

    @cached_property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self)

    @property
    def _is_32bit_index(self):
        blas_pkg = {
            "nvpl": "nvpl_blas",
        }.get(str(self.options.blas), str(self.options.blas))
        return self.dependencies[blas_pkg].options.get_safe("interface", "lp64") == "lp64"

    def config_options(self):
        if self.settings.arch not in ["x86_64", "x86"]:
            del self.options.with_fftw
        if self.settings.arch == "armv8":
            self.options.blas = "nvpl"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.cuda.requires("cudart")
        self.cuda.requires("cublas")
        self.cuda.requires("cufft")
        self.cuda.requires("cusolver")
        self.cuda.requires("curand")
        if self.options.with_nvtx:
            self.requires("nvtx/[^3]")
        if self.options.with_nvtiff:
            self.cuda.requires("nvtiff")
        if self.options.blas == "nvpl":
            self.requires("nvpl_blas/[<1]")
        elif self.options.blas == "blis":
            self.requires("blis/[<1]")
        elif self.options.blas == "openblas":
            self.requires("openblas/[<1]")
        if self.options.with_cutensor:
            self.cuda.requires("cutensornet")
            self.cuda.requires("cutensor")
        if self.options.with_cudss:
            self.cuda.requires("cudss")
        if self.options.get_safe("with_fftw"):
            self.requires("fftw/[>=3.3 <4]")
        if self.options.with_openmp:
            self.requires("openmp/system")

    def validate(self):
        check_min_cppstd(self, 17)
        if self.cuda.version < "11.8":
            raise ConanInvalidConfiguration("MatX requires CUDA 11.8 or higher")
        self.cuda.check_min_cuda_architecture(60)
        if self.options.blas == "nvpl":
            self.options["nvpl_blas"].interface = "ilp64"

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.23.1]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        # Skip cmake.install() to keep things simple and avoid a lot of patching
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        # Substitute for rapids_cmake_write_version_file(include/version_config.h),
        # but place it in a saner location.
        v = Version(self.version)
        save(self, os.path.join(self.package_folder, "include/matx/version_config.h"),
             textwrap.dedent(f"""
                #pragma once
                #define MATX_VERSION_MAJOR {v.major}
                #define MATX_VERSION_MINOR {v.minor}
                #define MATX_VERSION_PATCH {v.patch}
            """))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "matx")
        self.cpp_info.set_property("cmake_target_name", "matx::matx")
        self.cpp_info.includedirs.append("include/matx/kernels")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []

        if self.options.with_nvtx:
            self.cpp_info.defines.append("MATX_NVTX_FLAGS")
        if self._is_32bit_index:
            self.cpp_info.defines.append("MATX_INDEX_32_BIT")
        if self.options.with_openmp:
            self.cpp_info.defines.append("MATX_EN_OMP")
        if self.options.blas == "nvpl":
            self.cpp_info.defines.append("MATX_EN_NVPL")
            self.cpp_info.defines.append("NVPL_LAPACK_COMPLEX_CUSTOM")
        elif self.options.blas == "blis":
            self.cpp_info.defines.append("MATX_EN_BLIS")
        elif self.options.blas == "openblas":
            self.cpp_info.defines.append("MATX_EN_OPENBLAS")
        if self.options.get_safe("with_fftw"):
            self.cpp_info.defines.append("MATX_EN_X86_FFTW")
        if self.options.with_cutensor:
            self.cpp_info.defines.append("MATX_EN_CUTENSOR")
        if self.options.with_cudss:
            self.cpp_info.defines.append("MATX_EN_CUDSS")
        if self.options.with_nvtiff:
            self.cpp_info.defines.append("MATX_ENABLE_NVTIFF")
        if self.options.disable_cub_cache:
            self.cpp_info.defines.append("MATX_DISABLE_CUB_CACHE")
        if self.options.complex_op_nan_checks:
            self.cpp_info.defines.append("MATX_EN_COMPLEX_OP_NAN_CHECKS")
