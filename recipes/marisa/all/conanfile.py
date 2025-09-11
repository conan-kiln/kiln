import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class MarisaConan(ConanFile):
    name = "marisa"
    description = "Matching Algorithm with Recursively Implemented StorAge "
    license = "BSD-2-Clause OR LGPL-2.1"
    homepage = "https://github.com/s-yata/marisa-trie"
    topics = ("trie", "string-matching")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "enable_native": [True, False],
        "tools": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "enable_native": False,
        "tools": True,
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        replace_in_file(self, "CMakeLists.txt", "set(CMAKE_CXX_STANDARD 20)", "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["ENABLE_NATIVE_CODE"] = self.options.enable_native
        tc.variables["ENABLE_TOOLS"] = self.options.tools
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING.md", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "Marisa")
        self.cpp_info.set_property("cmake_target_name", "Marisa::marisa")
        self.cpp_info.set_property("pkg_config_name", "marisa")
        self.cpp_info.libs = ["marisa"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]
