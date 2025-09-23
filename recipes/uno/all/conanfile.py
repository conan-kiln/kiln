import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class UnoConan(ConanFile):
    name = "uno"
    description = "Uno (Unifying Nonlinear Optimization) - A modular optimization solver"
    license = "MIT"
    homepage = "https://github.com/cvanaret/Uno"
    topics = ("optimization", "nonlinear-programming", "mathematical-optimization", "solver")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_asl": [True, False],
        "with_bqpd": [True, False],
        "with_hsl": [True, False],
        "with_highs": [True, False],
        "with_mumps": [True, False],
        "with_metis": [True, False],
        "with_openmp": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_asl": False,
        "with_bqpd": True,
        "with_hsl": False,
        "with_highs": True,
        "with_mumps": False,
        "with_metis": True,
        "with_openmp": True,
    }
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("openblas/[<1]")
        if self.options.with_asl:
            self.requires("ampl-asl/[^1]")
        if self.options.with_bqpd:
            self.requires("bqpd_jll/[^1]")
        if self.options.with_hsl:
            self.requires("coin-hsl/[*]")
        if self.options.with_highs:
            self.requires("highs/[^1.7]")
        if self.options.with_mumps:
            self.requires("coin-mumps/[^3.0.5]")
        if self.options.with_metis:
            self.requires("metis/[^5.2.1]")
        if self.options.with_openmp:
            self.requires("openmp/system")

    def validate(self):
        check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        rm(self, "Find*.cmake", "cmake")
        replace_in_file(self, "CMakeLists.txt", "find_package(GTest CONFIG)", "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_STATIC_LIBS"] = not self.options.shared
        tc.cache_variables["BUILD_SHARED_LIBS"] = self.options.shared
        tc.cache_variables["WITH_ASL"] = self.options.with_asl
        tc.cache_variables["WITH_BQPD"] = self.options.with_bqpd
        tc.cache_variables["WITH_HIGHS"] = self.options.with_highs
        tc.cache_variables["WITH_HSL"] = self.options.with_hsl
        tc.cache_variables["WITH_METIS"] = self.options.with_metis
        tc.cache_variables["WITH_MUMPS"] = self.options.with_mumps
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("bqpd_jll", "cmake_file_name", "BQPD")
        deps.set_property("coin-hsl", "cmake_file_name", "HSL")
        deps.set_property("coin-hsl", "cmake_target_name", "HSL::HSL")
        deps.set_property("coin-mumps", "cmake_file_name", "MUMPS")
        deps.set_property("highs", "cmake_file_name", "HIGHS")
        deps.set_property("metis", "cmake_file_name", "METIS")
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        # Headers are not installed for some reason
        copy(self, "*.hpp", os.path.join(self.source_folder, "uno"), os.path.join(self.package_folder, "include", "uno"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["uno"]
        self.cpp_info.includedirs.append("include/uno")
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]
