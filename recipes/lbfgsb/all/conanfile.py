import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class LbfgsbConan(ConanFile):
    name = "lbfgsb"
    description = "L-BFGS-B is a limited-memory quasi-Newton code for bound-constrained optimization."
    license = "BSD-3-Clause"
    homepage = "https://users.iems.northwestern.edu/~nocedal/lbfgsb.html"
    topics = ("optimization", "quasi-newton", "bound-constrained")
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
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    @property
    def _fortran_compiler(self):
        executables = self.conf.get("tools.build:compiler_executables", default={}, check_type=dict)
        return executables.get("fortran")

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, self.export_sources_folder)

    def layout(self):
        cmake_layout(self, src_folder="src")

    # def requirements(self):
    #     self.requires("openblas/[>=0.3 <1]")

    def validate_build(self):
        if not self._fortran_compiler:
            raise ConanInvalidConfiguration(
                "A Fortran compiler is required. "
                "Please provide one by setting tools.build:compiler_executables={'fortran': '...'}."
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version])
        move_folder_contents(self, os.path.join(self.source_folder, "Lbfgsb.3.0"), self.source_folder)
        copy(self, "CMakeLists.txt", self.export_sources_folder, self.source_folder)

    def generate(self):
        tc = CMakeToolchain(self)
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
        self.cpp_info.libs = ["lbfgsb"]
        self.cpp_info.includedirs = []
        if not self.options.shared:
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.system_libs = ["m"]
            if "gfortran" in self._fortran_compiler:
                self.cpp_info.system_libs.append("gfortran")
