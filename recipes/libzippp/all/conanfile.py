import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class LibZipppConan(ConanFile):
    name = "libzippp"
    description = "A simple basic C++ wrapper around the libzip library"
    license = "BSD-3-Clause"
    homepage = "https://github.com/ctabin/libzippp"
    topics = ("zip", "zlib", "libzip", "zip-archives", "zip-editing")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_encryption": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_encryption": False,
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("zlib-ng/[^2.0]")
        self.requires("libzip/[^1]")

    def validate(self):
        check_min_cppstd(self, 11)
        if self.settings.compiler == "clang" and self.settings.compiler.get_safe("libcxx") == "libc++":
            raise ConanInvalidConfiguration(f"{self.ref} does not support clang with libc++. Use libstdc++ instead.")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.16 <5]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_CXX_STANDARD"] = 11
        tc.variables["LIBZIPPP_INSTALL"] = True
        tc.variables["LIBZIPPP_INSTALL_HEADERS"] = True
        tc.variables["LIBZIPPP_BUILD_TESTS"] = False
        tc.variables["LIBZIPPP_ENABLE_ENCRYPTION"] = self.options.with_encryption
        tc.variables["LIBZIPPP_CMAKE_CONFIG_MODE"] = True
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern="LICENCE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()

        rmdir(self, os.path.join(self.package_folder, "share"))
        rmdir(self, os.path.join(self.package_folder, "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "libzippp")
        self.cpp_info.set_property("cmake_target_name", "libzippp::libzippp")
        prefix = "lib" if self.settings.os == "Windows" else ""
        postfix = "" if self.options.shared else "_static"
        self.cpp_info.libs = [f"{prefix}zippp{postfix}"]

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("m")

        if self.options.with_encryption:
            self.cpp_info.defines.append("LIBZIPPP_WITH_ENCRYPTION")
