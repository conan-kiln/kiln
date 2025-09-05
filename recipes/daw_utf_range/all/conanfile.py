import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"

class DawUtfRangeConan(ConanFile):
    name = "daw_utf_range"
    description = "Range operations on character arrays"
    license = "BSL-1.0"
    homepage = "https://github.com/beached/utf_range/"
    topics = ("utf", "validator", "iterator", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        corresponding_daw_header_version = self.conan_data["daw_headers_mapping"][self.version]
        self.requires(f"daw_header_libraries/{corresponding_daw_header_version}")

    def package_id(self):
        self.info.clear()

    def validate(self):
        check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["DAW_USE_PACKAGE_MANAGEMENT"] = True
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()

    def package(self):
        copy(self, pattern="LICENSE*", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.set_property("cmake_file_name", "daw-utf-range")
        self.cpp_info.set_property("cmake_target_name", "daw::daw-utf-range")
