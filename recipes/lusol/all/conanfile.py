import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.4"


class LusolConan(ConanFile):
    name = "lusol"
    description = "LUSOL maintains LU factors of a square or rectangular sparse matrix"
    license = "MIT OR BSD-3-Clause"
    homepage = "http://web.stanford.edu/group/SOL/software/lusol/"
    topics = ("linear-algebra", "sparse-matrix", "lu-factorization", "numerical")
    package_type = "static-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "fPIC": [True, False],
    }
    default_options = {
        "fPIC": True,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))

    def layout(self):
        cmake_layout(self, src_folder="src")

    @property
    def _fortran_compiler(self):
        return self.conf.get("tools.build:compiler_executables", default={}, check_type=dict).get("fortran", None)

    def requirements(self):
        self.requires("lapack/latest")

    def validate_build(self):
        if not self._fortran_compiler:
            raise ConanInvalidConfiguration(
                "A Fortran compiler is required. "
                "Please add one to `tools.build:compiler_executables={'fortran': '...'}`."
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE*", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["clusol"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]
        if "gfortran" in self._fortran_compiler:
            self.cpp_info.system_libs.append("gfortran")
