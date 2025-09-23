import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class MatlabMockupConan(ConanFile):
    name = "matlab-mockup"
    description = "Mockup interface for MATLAB"
    license = "MIT"
    homepage = "https://github.com/casadi/mockups"
    topics = ("matlab", "mockup", "casadi")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder="matlab")
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "cmake"))

    def package_info(self):
            self.cpp_info.set_property("cmake_file_name", "matlab")
            self.cpp_info.set_property("cmake_target_name", "matlab::matlab")

            self.cpp_info.components["mex"].set_property("cmake_target_name", "matlab::mex")
            self.cpp_info.components["mex"].libs = ["mex"]
            self.cpp_info.components["mex"].defines = ["MATLAB_API_VERSION=800"]

            self.cpp_info.components["mx"].set_property("cmake_target_name", "matlab::mx")
            self.cpp_info.components["mx"].libs = ["mx"]
            self.cpp_info.components["mx"].defines = ["MATLAB_API_VERSION=800"]

            self.cpp_info.components["ut"].set_property("cmake_target_name", "matlab::ut")
            self.cpp_info.components["ut"].libs = ["ut"]

            self.cpp_info.components["eng"].set_property("cmake_target_name", "matlab::eng")
            self.cpp_info.components["eng"].libs = ["eng"]
