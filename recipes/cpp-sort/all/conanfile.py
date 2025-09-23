import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc

required_conan_version = ">=2.1"


class CppSortConan(ConanFile):
    name = "cpp-sort"
    description = "Additional sorting algorithms & related tools"
    license = "MIT"
    homepage = "https://github.com/Morwenn/cpp-sort"
    topics = ("sorting", "algorithms", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        cmake_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def validate(self):
        check_min_cppstd(self, 14)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_TESTING"] = "OFF"
        tc.generate()

    def package(self):
        copy(self, "LICENSE.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "NOTICE.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.configure()
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "cpp-sort")
        self.cpp_info.set_property("cmake_target_name", "cpp-sort::cpp-sort")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        if is_msvc(self):
            self.cpp_info.cxxflags = ["/permissive-"]
