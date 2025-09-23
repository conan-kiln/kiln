import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.4"


class LibccdConan(ConanFile):
    name = "libccd"
    description = "Library for collision detection between two convex shapes."
    license = "BSD-3-Clause"
    topics = ("collision", "3d")
    homepage = "https://github.com/danfis/libccd"
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "double_precision": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "double_precision": False,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        replace_in_file(self, "CMakeLists.txt",
                        "cmake_minimum_required(VERSION 2.8.11)",
                        "cmake_minimum_required(VERSION 3.5)")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_DOCUMENTATION"] = False
        tc.variables["ENABLE_DOUBLE_PRECISION"] = self.options.double_precision
        tc.variables["CCD_HIDE_ALL_SYMBOLS"] = not self.options.shared
        if self.settings.os in ["Linux", "FreeBSD"]:
            tc.variables["LIBM_LIBRARY"] = "m"
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "BSD-LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "ccd"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "ccd")
        self.cpp_info.set_property("cmake_target_name", "ccd")
        self.cpp_info.set_property("pkg_config_name", "ccd")
        self.cpp_info.libs = ["ccd"]
        if not self.options.shared:
            self.cpp_info.defines.append("CCD_STATIC_DEFINE")
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("m")
