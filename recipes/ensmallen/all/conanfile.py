import os

from conan import ConanFile
from conan.tools.cmake import CMakeToolchain, CMake, cmake_layout, CMakeDeps
from conan.tools.files import *

required_conan_version = ">=2.1"


class EnsmallenRecipe(ConanFile):
    name = "ensmallen"
    description = "ensmallen is a high quality C++ library for non-linear numerical optimization."
    license = "BSD-3-Clause"
    homepage = "https://github.com/mlpack/ensmallen"
    topics = ("optimization", "numerical", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"

    def package_id(self):
        self.info.clear()

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("armadillo/[*]")
        self.requires("openmp/system")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["USE_OPENMP"] = True
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()

    def package(self):
        copy(self, "LICENSE.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
