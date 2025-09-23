import os

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class CmrcConan(ConanFile):
    name = "cmrc"
    description = "A Resource Compiler in a Single CMake Script"
    license = "MIT"
    homepage = "https://github.com/vector-of-bool/cmrc"
    topics = ("cmake", "resource-compiler")
    package_type = "build-scripts"
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "CMakeRC.cmake", self.source_folder, os.path.join(self.package_folder, "share", "cmrc"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "CMakeRC")
        self.cpp_info.includedirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.builddirs = ["share/cmrc"]
        self.cpp_info.set_property("cmake_build_modules", ["share/cmrc/CMakeRC.cmake"])
