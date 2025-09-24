import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class LibCuckooConan(ConanFile):
    name = "libcuckoo"
    description = "A high-performance, concurrent hash table"
    license = "Apache-2.0"
    homepage = "https://github.com/efficient/libcuckoo"
    topics = ("concurrency", "hashmap", "header-only", "library", "cuckoo")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def validate(self):
        check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        replace_in_file(self, "CMakeLists.txt",
                        "cmake_minimum_required(VERSION 3.1.0)",
                        "cmake_minimum_required(VERSION 3.5.0)")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_EXAMPLES"] = False
        tc.variables["BUILD_STRESS_TESTS"] = False
        tc.variables["BUILD_TESTS"] = False
        tc.variables["BUILD_UNIT_TESTS"] = False
        tc.variables["BUILD_UNIVERSAL_BENCHMARK"] = False
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))


    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "libcuckoo")
        self.cpp_info.set_property("cmake_target_name", "libcuckoo::libcuckoo")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        if self.settings.os == "Linux":
            self.cpp_info.system_libs = ["pthread"]
