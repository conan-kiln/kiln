import os

from conan import ConanFile
from conan.tools.build import check_min_cstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class CelloConan(ConanFile):
    name = "cello"
    description = "Cello is a library that brings higher level programming to C."
    license = "BSD-3-Clause"
    homepage = "https://libcello.org/"
    topics = ("data-structures", "polymorphic-functions", "object-oriented-programming", "garbage-collection", "exceptions", "reflection")
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

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        if self.settings.get_safe("compiler.cstd"):
            check_min_cstd(self, 99)

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
        copy(self, "LICENSE.md", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "Cello")  # unofficial
        self.cpp_info.set_property("cmake_target_aliases", ["Cello"])
        self.cpp_info.libs = ["Cello"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m", "pthread"]
            if self.settings.os == "FreeBSD" and self.settings.build_type == "Debug":
                self.cpp_info.system_libs.append("execinfo")
        elif self.settings.os == "Windows":
            self.cpp_info.system_libs = ["pthread"]
            if self.settings.build_type == "Debug":
                self.cpp_info.system_libs.append("DbgHelp")
