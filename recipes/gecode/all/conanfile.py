import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class GecodeConan(ConanFile):
    name = "gecode"
    description = "Generic constraint programming toolkit"
    license = "MIT"
    homepage = "https://www.gecode.org"
    topics = ("constraint-programming", "optimization", "search", "csp")
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
        replace_in_file(self, "CMakeLists.txt",
                        "cmake_minimum_required(VERSION 2.8.8)",
                        "cmake_minimum_required(VERSION 3.5)")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_TESTING"] = False
        tc.cache_variables["BUILD_EXAMPLES"] = False
        tc.cache_variables["ENABLE_GIST"] = False
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE*", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.components["support"].libs = ["gecodesupport"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["support"].system_libs = ["m"]

        self.cpp_info.components["kernel"].libs = ["gecodekernel"]
        self.cpp_info.components["kernel"].requires = ["support"]

        self.cpp_info.components["search"].libs = ["gecodesearch"]
        self.cpp_info.components["search"].requires = ["kernel"]

        self.cpp_info.components["int"].libs = ["gecodeint"]
        self.cpp_info.components["int"].requires = ["kernel"]

        self.cpp_info.components["set"].libs = ["gecodeset"]
        self.cpp_info.components["set"].requires = ["int"]

        self.cpp_info.components["float"].libs = ["gecodefloat"]
        self.cpp_info.components["float"].requires = ["int"]

        self.cpp_info.components["minimodel"].libs = ["gecodeminimodel"]
        self.cpp_info.components["minimodel"].requires = ["int", "search", "set", "float"]

        self.cpp_info.components["driver"].libs = ["gecodedriver"]
        self.cpp_info.components["driver"].requires = ["int"]

        self.cpp_info.components["flatzinc"].libs = ["gecodeflatzinc"]
        self.cpp_info.components["flatzinc"].requires = ["minimodel", "driver"]
