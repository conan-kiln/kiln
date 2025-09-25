import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd, valid_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class GuanaqoConan(ConanFile):
    name = "guanaqo"
    description = "Utilities for scientific software."
    license = "LGPL-3.0-or-later"
    homepage = "https://github.com/tttapa/guanaqo"
    topics = ("scientific-programming", "alpaqa")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "precision_quad": [True, False],
        "with_blas": [True, False],
        "with_openmp": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "precision_quad": False,
        "with_blas": True,
        "with_openmp": True,
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_openmp:
            self.requires("openmp/system")
        if self.options.with_blas:
            self.requires("lapack/latest", transitive_headers=True)

    def validate(self):
        check_min_cppstd(self, 20, gnu_extensions=self.options.precision_quad)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.24 <5]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        download(self, **self.conan_data["license"][0], filename="LICENSE")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["GUANAQO_WITH_CXX_23"] = valid_min_cppstd(self, 23)
        tc.cache_variables["GUANAQO_WITH_TESTS"] = False
        tc.cache_variables["GUANAQO_WITH_BLAS"] = self.options.with_blas
        tc.cache_variables["GUANAQO_WITH_OPENMP"] = self.options.with_openmp
        if self.options.with_blas:
            blas_provider = str(self.dependencies["blas"].options.provider)
            tc.cache_variables["GUANAQO_WITH_OPENBLAS"] = blas_provider == "openblas"
            tc.cache_variables["GUANAQO_WITH_MKL"] = blas_provider == "mkl"
            is_64bit = self.dependencies["blas"].options.interface == "ilp64"
            tc.cache_variables["GUANAQO_BLAS_INDEX_TYPE"] = "long long" if is_64bit else "int"
        tc.cache_variables["GUANAQO_WITH_TRACING"] = False
        tc.cache_variables["GUANAQO_WITH_ITT"] = False
        tc.cache_variables["GUANAQO_WITH_QUAD_PRECISION"] = self.options.precision_quad
        tc.variables["CMAKE_DISABLE_FIND_PACKAGE_Doxygen"] = True
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    @property
    def _lib_suffix(self):
        return {
            "Debug": "_d",
            "RelWithDebInfo": "_rd",
            "MinSizeRel": "_rs",
        }.get(str(self.settings.build_type), "")

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "guanaqo")
        self.cpp_info.set_property("cmake_target_name", "guanaqo::guanaqo")
        self.cpp_info.set_property("cmake_additional_variables_prefixes", ["guanaqoCore", "guanaqoBLAS"])

        self.cpp_info.components["core"].set_property("cmake_target_aliases", ["guanaqo::linalg"])
        self.cpp_info.components["core"].libs = ["guanaqo" + self._lib_suffix]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["core"].system_libs = ["m"]
        if self.options.precision_quad:
            self.cpp_info.components["core"].defines.append("GUANAQO_WITH_QUAD_PRECISION")
        if self.options.with_openmp:
            self.cpp_info.components["core"].requires.append("openmp::openmp")
            self.cpp_info.components["core"].defines.append("GUANAQO_WITH_OPENMP")
        if self.options.get_safe("with_itt"):
            self.cpp_info.components["core"].defines.append("GUANAQO_WITH_ITT")
        if self.options.get_safe("tracing"):
            self.cpp_info.components["core"].defines.append("GUANAQO_WITH_TRACING")

        if self.options.with_blas:
            self.cpp_info.components["blas"].set_property("cmake_target_name", "guanaqo::blas")
            self.cpp_info.components["blas"].set_property("cmake_target_aliases", ["guanaqo::blas-lapack-lib"])
            self.cpp_info.components["blas"].libs = ["guanaqo-blas" + self._lib_suffix]
            # self.cpp_info.components["blas"].defines.append("GUANAQO_WITH_HL_BLAS_TRACING")
            self.cpp_info.requires = ["core"]
            if self.options.with_blas:
                self.cpp_info.components["blas"].requires.append("blas::blas")
                self.cpp_info.components["blas"].defines.append("GUANAQO_WITH_BLAS")
                blas_provider = str(self.dependencies["blas"].options.provider)
                if blas_provider == "openblas":
                    self.cpp_info.components["blas"].defines.append("GUANAQO_WITH_OPENBLAS")
                elif blas_provider == "mkl":
                    self.cpp_info.components["blas"].defines.append("GUANAQO_WITH_MKL")
