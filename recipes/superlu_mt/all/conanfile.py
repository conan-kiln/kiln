import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class SuperLuMtConan(ConanFile):
    name = "superlu_mt"
    description = "SuperLU_MT is a parallel extension to the serial SuperLU library."
    license = "BSD-3-Clause"
    homepage = "https://github.com/xiaoyeli/superlu_mt"
    topics = ("linear-algebra", "sparse-matrix", "lu-factorization", "scientific-computing", "parallel")
    provides = ["superlu"]
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "threading": ["pthread", "openmp"],
        "enable_single": [True, False],
        "enable_double": [True, False],
        "enable_complex": [True, False],
        "enable_complex16": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "threading": "openmp",
        "enable_single": True,
        "enable_double": True,
        "enable_complex": True,
        "enable_complex16": True,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def export_sources(self):
        copy(self, "conan_deps.cmake", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("openblas/[*]")
        if self.options.threading == "openmp":
            self.requires("openmp/system")

    def validate(self):
        if self.settings.get_safe("compiler.cstd"):
            check_min_cstd(self, 99)
        if not any([self.options.enable_single, self.options.enable_double,
                    self.options.enable_complex, self.options.enable_complex16]):
            raise ConanInvalidConfiguration("At least one precision variant must be enabled")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["CMAKE_PROJECT_SuperLU_MT_INCLUDE"] = "conan_deps.cmake"
        tc.cache_variables["PLAT"] = "_OPENMP" if self.options.threading == "openmp" else "_PTHREAD"
        tc.cache_variables["enable_tests"] = False
        tc.cache_variables["enable_examples"] = False
        tc.cache_variables["enable_doc"] = False
        tc.cache_variables["enable_matlabmex"] = False
        tc.cache_variables["enable_single"] = self.options.enable_single
        tc.cache_variables["enable_double"] = self.options.enable_double
        tc.cache_variables["enable_complex"] = self.options.enable_complex
        tc.cache_variables["enable_complex16"] = self.options.enable_complex16
        tc.cache_variables["enable_fortran"] = False
        tc.cache_variables["enable_internal_blaslib"] = False
        tc.cache_variables["TPL_ENABLE_INTERNAL_BLASLIB"] = False
        tc.cache_variables["TPL_BLAS_LIBRARIES"] = "OpenBLAS::OpenBLAS"
        tc.cache_variables["LONGINT"] = self.dependencies["openblas"].options.interface == "ilp64"
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "License.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "superlu_mt")
        self.cpp_info.set_property("cmake_target_name", "superlu_mt::superlu_mt")
        self.cpp_info.set_property("pkg_config_name", "superlu_mt")
        libname = "superlu_mt"
        libname += "_OPENMP" if self.options.threading == "openmp" else "_PTHREAD"
        self.cpp_info.libs = [libname]
        self.cpp_info.includedirs.append("include/superlu_mt")
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m", "pthread"]
