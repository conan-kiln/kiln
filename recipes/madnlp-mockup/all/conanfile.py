import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class MadNlpConan(ConanFile):
    name = "madnlp-mockup"
    description = "Mockup interface for MadNLP: a solver for nonlinear programming with GPU support"
    license = "MIT"
    homepage = "https://github.com/casadi/mockups"
    topics = ("optimization", "casadi", "nonlinear-optimization")
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
        cmake.configure(build_script_folder="madnlp")
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "madnlp")
        self.cpp_info.set_property("cmake_target_name", "madnlp::madnlp")
        self.cpp_info.components["madnlp_c"].set_property("cmake_target_name", "madnlp::madnlp_c")
        self.cpp_info.components["madnlp_c"].libs = ["madnlp_c"]
