import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class QpmadConan(ConanFile):
    name = "qpmad"
    description = "Eigen-based, header-only C++ implementation of Goldfarb-Idnani dual active set algorithm for quadratic programming"
    license = "MIT"
    homepage = "https://github.com/asherikov/qpmad"
    topics = ("quadratic-programming", "optimization", "eigen", "goldfarb-idnani", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "enable_tracing": [True, False],
        "use_householder": [True, False],
    }
    default_options = {
        "enable_tracing": False,
        "use_householder": False,
    }

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("eigen/[>=3.3 <6]")

    def validate(self):
        check_min_cppstd(self, 14)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        replace_in_file(self, "CMakeLists.txt",
                        "cmake_minimum_required(VERSION 3.0)",
                        "cmake_minimum_required(VERSION 3.5)")
        replace_in_file(self, "CMakeLists.txt", 'include_directories (SYSTEM "${EIGEN3_INCLUDE_DIR}")', "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["QPMAD_BUILD_TESTS"] = False
        tc.cache_variables["QPMAD_ENABLE_TRACING"] = self.options.enable_tracing
        tc.cache_variables["QPMAD_USE_HOUSEHOLDER"] = self.options.use_householder
        tc.cache_variables["QPMAD_PEDANTIC_LICENSE"] = False  # handled by eigen/*:MPL2_only
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
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "qpmad")
        self.cpp_info.libdirs = []
        self.cpp_info.bindirs = []
