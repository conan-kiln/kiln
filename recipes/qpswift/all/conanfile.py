import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.4"


class QpSwiftConan(ConanFile):
    name = "qpswift"
    description = "qpSWIFT is light-weight sparse Quadratic Programming solver targeted for embedded and robotic applications."
    license = "GPL-3.0-only"
    homepage = "https://github.com/qpSWIFT/qpSWIFT"
    topics = ("quadratic-programming", "optimization", "embedded", "robotics", "sparse-solver")
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
    languages = ["C"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("suitesparse-ldl/[^3]", transitive_headers=True)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        replace_in_file(self, "CMakeLists.txt", "set(CMAKE_", "# set(CMAKE_")
        # Unvendor SuiteSparse LDL
        rm(self, "amd_*.c", "src")
        rm(self, "amd*.h", "include")
        os.unlink("include/SuiteSparse_config.h")
        os.unlink("include/ldl.h")
        os.unlink("src/ldl.c")
        replace_in_file(self, "include/Auxilary.h", '#include "amd_internal.h"', "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["QPTESTS"] = False
        tc.cache_variables["QPDEMOS"] = False
        tc.cache_variables["QPSHAREDLIB"] = self.options.shared
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
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "qpSWIFT")
        self.cpp_info.set_property("cmake_target_name", "qpSWIFT::qpSWIFT")
        self.cpp_info.set_property("cmake_target_aliases", ["qpSWIFT::qpSWIFT-shared", "qpSWIFT::qpSWIFT-static"])
        self.cpp_info.libs = ["qpSWIFT"]
        self.cpp_info.includedirs.append("include/qpSWIFT")
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m", "rt", "dl"]
