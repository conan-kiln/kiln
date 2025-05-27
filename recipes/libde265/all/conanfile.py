import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd, stdcpp_library
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class Libde265Conan(ConanFile):
    name = "libde265"
    description = "Open h.265 video codec implementation."
    license = "LGPL-3.0-or-later"
    topics = ("codec", "video", "h.265")
    homepage = "https://github.com/strukturag/libde265"
    url = "https://github.com/conan-io/conan-center-index"
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "sse": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "sse": True,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if self.settings.arch not in ["x86", "x86_64"]:
            del self.options.sse

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        replace_in_file(self, "CMakeLists.txt", "set(CMAKE_POSITION_INDEPENDENT_CODE ON)", "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_POSITION_INDEPENDENT_CODE"] = self.options.get_safe("fPIC", True)
        tc.variables["ENABLE_SDL"] = False
        tc.variables["DISABLE_SSE"] = not self.options.get_safe("sse", False)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "libde265")
        self.cpp_info.set_property("cmake_target_name", "de265")
        self.cpp_info.set_property("cmake_target_aliases", ["libde265"]) # official imported target before 1.0.10
        self.cpp_info.set_property("pkg_config_name", "libde265")
        version = Version(self.version)
        prefix = "lib" if (version < "1.0.10" or (version > "1.0.11" and self.settings.os == "Windows" and not self.options.shared)) else ""
        self.cpp_info.libs = [f"{prefix}de265"]
        if not self.options.shared:
            self.cpp_info.defines = ["LIBDE265_STATIC_BUILD"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m", "pthread"]
        if not self.options.shared:
            libcxx = stdcpp_library(self)
            if libcxx:
                self.cpp_info.system_libs.append(libcxx)
