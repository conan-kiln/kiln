import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class crc32cConan(ConanFile):
    name = "crc32c"
    description = "CRC32C implementation with support for CPU-specific acceleration instructions"
    topics = ("crc32c", "crc")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/google/crc32c"
    license = "BSD-3-Clause"

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

    def validate(self):
        check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # For CMake v4 support
        replace_in_file(self, "CMakeLists.txt",
            "cmake_minimum_required(VERSION 3.1)",
            "cmake_minimum_required(VERSION 3.5)")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CRC32C_BUILD_TESTS"] = False
        tc.variables["CRC32C_BUILD_BENCHMARKS"] = False
        tc.variables["CRC32C_INSTALL"] = True
        tc.variables["CRC32C_USE_GLOG"] = False
        tc.variables["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = True
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "Crc32c")
        self.cpp_info.set_property("cmake_target_name", "Crc32c::crc32c")
        self.cpp_info.libs = ["crc32c"]
