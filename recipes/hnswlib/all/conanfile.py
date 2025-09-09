import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class HnswlibConan(ConanFile):
    name = "hnswlib"
    description = "Header-only C++ library for fast approximate nearest neighbors"
    license = "Apache-2.0"
    homepage = "https://github.com/nmslib/hnswlib"
    topics = ("nearest-neighbor", "hnsw", "approximate", "ann", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        check_min_cppstd(self, 11)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.0]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        # CMake v4 support
        replace_in_file(self, "CMakeLists.txt",
                        "cmake_minimum_required(VERSION 3.0...3.26)",
                        "cmake_minimum_required(VERSION 3.15)")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["HNSWLIB_EXAMPLES"] = False
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "hnswlib")
        self.cpp_info.set_property("cmake_target_name", "hnswlib::hnswlib")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
