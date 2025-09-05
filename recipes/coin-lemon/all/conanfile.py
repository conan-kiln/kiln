import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class CoinLemonConan(ConanFile):
    name = "coin-lemon"
    license = "BSL-1.0"
    homepage = "http://lemon.cs.elte.hu"
    description = "LEMON stands for Library for Efficient Modeling and Optimization in Networks."
    topics = ("data structures", "algorithms", "graphs", "network")

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

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        # CMake v4 support
        replace_in_file(self, "CMakeLists.txt",
                        "CMAKE_MINIMUM_REQUIRED(VERSION 2.8)",
                        "CMAKE_MINIMUM_REQUIRED(VERSION 3.5)")
        replace_in_file(self, "CMakeLists.txt", "CMAKE_POLICY(SET CMP0048 OLD)", "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["LEMON_ENABLE_GLPK"] = False
        tc.variables["LEMON_ENABLE_ILOG"] = False
        tc.variables["LEMON_ENABLE_COIN"] = False
        tc.variables["LEMON_ENABLE_SOPLEX"] = False
        # For msvc shared
        tc.variables["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = True
        tc.generate()

    def _patch_sources(self):
        # Disable demo, tools, doc & test
        replace_in_file(
            self,
            os.path.join(self.source_folder, "CMakeLists.txt"),
            "IF(${CMAKE_SOURCE_DIR} STREQUAL ${PROJECT_SOURCE_DIR})",
            "if(0)",
        )

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "cmake"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "LEMON")
        self.cpp_info.set_property("cmake_target_name", "LEMON::LEMON") # no official target name actually
        self.cpp_info.set_property("pkg_config_name", "lemon")
        self.cpp_info.libs = ["lemon" if self.settings.os == "Windows" else "emon"]
        self.cpp_info.defines.append("LEMON_ONLY_TEMPLATES")
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("m")
