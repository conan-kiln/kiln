import os

from conan import ConanFile
from conan.tools.build import stdcpp_library
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class MeshOptimizerConan(ConanFile):
    name = "meshoptimizer"
    description = "Mesh optimization library that makes meshes smaller and faster to render"
    topics = ("mesh", "optimizer", "3d")
    homepage = "https://github.com/zeux/meshoptimizer"
    license = "MIT"

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

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # CMake v4 support
        if Version(self.version) < "0.20":
            replace_in_file(self, "CMakeLists.txt",
                            "cmake_minimum_required(VERSION 3.0)",
                            "cmake_minimum_required(VERSION 3.5)")
        # No warnings as errors - now fine in 0.19 and up
        if Version(self.version) < "0.19":
            cmakelists = os.path.join(self.source_folder, "CMakeLists.txt")
            replace_in_file(self, cmakelists, "add_compile_options(/W4 /WX)", "")
            replace_in_file(self, cmakelists, "-Werror", "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["MESHOPT_BUILD_SHARED_LIBS"] = self.options.shared
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE.md", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rm(self, "*.pdb", os.path.join(self.package_folder, "bin"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "meshoptimizer")
        self.cpp_info.set_property("cmake_target_name", "meshoptimizer::meshoptimizer")
        self.cpp_info.libs = ["meshoptimizer"]
        if not self.options.shared:
            libcxx = stdcpp_library(self)
            if libcxx:
                self.cpp_info.system_libs.append(libcxx)
        if self.options.shared and self.settings.os == "Windows":
            self.cpp_info.defines = ["MESHOPTIMIZER_API=__declspec(dllimport)"]
