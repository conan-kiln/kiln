import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.4"


class OpenSpecfunConan(ConanFile):
    name = "openspecfun"
    description = "OpenSpecfun provides a collection of special mathematical functions from the AMOS and Faddeeva libraries."
    license = "MIT"
    homepage = "https://github.com/JuliaMath/openspecfun"
    topics = ("math", "transcendental-functions", "complex-functions")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }
    provides = ["amos", "faddeeva"]
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    @property
    def _fortran_compiler(self):
        executables = self.conf.get("tools.build:compiler_executables", default={}, check_type=dict)
        return executables.get("fortran")

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if not self._fortran_compiler:
            self.requires("gfortran/[*]")

    def build_requirements(self):
        if not self._fortran_compiler:
            self.tool_requires("gfortran/[*]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE.md", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["openspecfun"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]
        if not self._fortran_compiler:
            self.cpp_info.system_libs.append("gfortran")
