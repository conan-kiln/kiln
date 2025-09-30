import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class LibnaboConan(ConanFile):
    name = "libnabo"
    description = "A fast K Nearest Neighbor library for low-dimensional spaces"
    license = "BSD-3-Clause"
    homepage = "https://github.com/ethz-asl/libnabo"
    topics = ("nearest-neighbor", "kd-tree")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_openmp": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_openmp": True,
    }
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("eigen/[>=3.3 <6]", transitive_headers=True)
        if self.options.with_openmp:
            # Only used in .cpp files
            self.requires("openmp/system")

    def validate(self):
        check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        replace_in_file(self, "CMakeLists.txt", "set (CMAKE_CXX_STANDARD 11)", "")
        replace_in_file(self, "nabo/kdtree_cpu.cpp", "#include <utility>", "#include <utility>\n#include <cassert>")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["USE_OPEN_MP"] = self.options.with_openmp
        tc.cache_variables["USE_OPEN_CL"] = False
        tc.cache_variables["SHARED_LIBS"] = self.options.shared
        if Version(self.version) >= "1.1.0":
            tc.variables["LIBNABO_BUILD_DOXYGEN"] = False
            tc.variables["LIBNABO_BUILD_EXAMPLES"] = False
            tc.variables["LIBNABO_BUILD_TESTS"] = False
            tc.variables["LIBNABO_BUILD_PYTHON"] = False
            tc.variables["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = True
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "copyright", src=os.path.join(self.source_folder, "debian"),
                                dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "libnabo")
        self.cpp_info.set_property("cmake_target_name", "libnabo::nabo")
        self.cpp_info.libs = ["nabo"]
