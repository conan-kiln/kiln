import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.4"

class NanomsgConan(ConanFile):
    name = "nanomsg"
    description = "A socket library that provides several common communication patterns."
    license = "MIT"
    homepage = "https://github.com/nanomsg/nanomsg"
    topics = ("socket", "protocols", "communication")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "enable_coverage": [True, False],
        "enable_getaddrinfo_a":[True, False],
        "enable_tools": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "enable_coverage": False,
        "enable_getaddrinfo_a":True,
        "enable_tools": False,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        replace_in_file(self, "CMakeLists.txt",
                        "cmake_minimum_required (VERSION 2.8.12)",
                        "cmake_minimum_required (VERSION 3.5)")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["NN_STATIC_LIB"] = not self.options.shared
        tc.variables["NN_ENABLE_COVERAGE"] = self.options.enable_coverage
        tc.variables["NN_ENABLE_GETADDRINFO_A"] = self.options.enable_getaddrinfo_a
        tc.variables["NN_ENABLE_DOC"] = False
        tc.variables["NN_TESTS"] = False
        tc.variables["NN_TOOLS"] = self.options.enable_tools
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern="COPYING", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()

        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        rm(self, "*.la", os.path.join(self.package_folder, "lib"))
        rm(self, "*.pdb", os.path.join(self.package_folder, "lib"))
        rm(self, "*.pdb", os.path.join(self.package_folder, "bin"))

    def package_info(self):
        self.cpp_info.libs = ["nanomsg"]
        self.cpp_info.set_property("cmake_file_name", "nanomsg")
        self.cpp_info.set_property("cmake_target_name", "nanomsg::nanomsg")
        self.cpp_info.set_property("pkg_config_name", "nanomsg")

        if self.settings.os == "Windows" and not self.options.shared:
            self.cpp_info.system_libs.extend(["mswsock", "ws2_32", "advapi32"])
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("pthread")
            self.cpp_info.system_libs.append("anl")
            self.cpp_info.system_libs.append("rt")

        if not self.options.shared:
            self.cpp_info.defines.append("NN_STATIC_LIB")
        if self.options.enable_coverage:
            self.cpp_info.defines.append("NN_ENABLE_COVERAGE")
