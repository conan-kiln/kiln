import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class HpipmConan(ConanFile):
    name = "hpipm"
    description = "High-Performance Interior Point Method solver for dense, optimal control- and tree-structured convex quadratic programs"
    license = "BSD-2-Clause"
    homepage = "https://github.com/giaf/hpipm"
    topics = ("optimization", "quadratic-programming", "interior-point", "model-predictive-control")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "target": ["avx", "generic"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "target": "avx",
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if self.settings.arch != "x86_64":
            self.options.target = "generic"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("blasfeo/[>=0.1 <1]", transitive_headers=True, transitive_libs=True)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_SHARED_LIBS"] = self.options.shared
        tc.cache_variables["TARGET"] = str(self.options.target).upper()
        tc.cache_variables["USE_C99_MATH"] = True
        tc.cache_variables["HPIPM_TESTING"] = False
        tc.cache_variables["HPIPM_FIND_BLASFEO"] = True
        tc.cache_variables["CMAKE_INSTALL_PREFIX"] = self.package_folder.replace("\\", "/")
        tc.cache_variables["CMAKE_TRY_COMPILE_CONFIGURATION"] = str(self.settings.build_type)
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
        rmdir(self, os.path.join(self.package_folder, "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "hpipm")
        self.cpp_info.set_property("cmake_target_name", "hpipm")
        self.cpp_info.libs = ["hpipm"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]
