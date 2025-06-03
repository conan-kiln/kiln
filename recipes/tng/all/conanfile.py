import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.4"


class tngConan(ConanFile):
    name = "tng"
    description = "External GROMACS library for loading tng files."
    license = "BSD-3-Clause"
    topics = ("tng", "gromacs")
    homepage = "https://gitlab.com/gromacs/tng/"
    url = "https://github.com/conan-io/conan-center-index"

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
    languages = ["C"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("zlib/[>=1.2.11 <2]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        # CMake v4 support
        replace_in_file(self, "CMakeLists.txt",
                        "cmake_minimum_required(VERSION 3.1)",
                        "cmake_minimum_required(VERSION 3.5)")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["TNG_BUILD_OWN_ZLIB"] = False
        tc.variables["TNG_BUILD_EXAMPLES"] = False
        tc.variables["TNG_BUILD_TEST"] = False
        # Honor BUILD_SHARED_LIBS from conan_toolchain (see https://github.com/conan-io/conan/issues/11840)
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0077"] = "NEW"
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "tng_io")
        self.cpp_info.set_property("cmake_target_name", "tng_io::tng_io")
        self.cpp_info.libs = ["tng_io"]
        if self.settings.os in ("Linux", "FreeBSD"):
            self.cpp_info.system_libs = ["m"]
