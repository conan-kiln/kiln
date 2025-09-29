import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd, stdcpp_library
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class PiqpConan(ConanFile):
    name = "piqp"
    description = "PIQP: Proximal Interior Point Quadratic Programming solver"
    license = "BSD-2-Clause"
    homepage = "https://github.com/PREDICT-EPFL/piqp"
    topics = ("optimization", "quadratic-programming", "interior-point", "solver")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "header_only": [True, False],
        "shared": [True, False],
        "fPIC": [True, False],
        "c_interface": [True, False],
        "with_blasfeo": [True, False],
        "with_openmp": [True, False],
    }
    default_options = {
        "header_only": False,
        "shared": False,
        "fPIC": True,
        "c_interface": True,
        "with_blasfeo": True,
        "with_openmp": True,
    }
    implements = ["auto_shared_fpic", "auto_header_only"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("eigen/[>=3.3 <6]", transitive_headers=True)
        if self.options.with_blasfeo:
            self.requires("blasfeo/[>=0.1 <1]", transitive_headers=True, transitive_libs=True)
        if self.options.with_openmp:
            self.requires("openmp/system", transitive_headers=True, transitive_libs=True)

    def validate(self):
        check_min_cppstd(self, 17)
        if self.options.c_interface and self.options.header_only:
            raise ConanInvalidConfiguration("c_interface=True requires header_only=False")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.21]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        replace_in_file(self, "include/piqp/dense/ldlt_no_pivot.hpp", "EIGEN_NOEXCEPT", "noexcept")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_WITH_TEMPLATE_INSTANTIATION"] = not self.options.header_only
        tc.cache_variables["BUILD_WITH_BLASFEO"] = self.options.with_blasfeo
        tc.cache_variables["BUILD_WITH_OPENMP"] = self.options.with_openmp
        tc.cache_variables["BUILD_WITH_STD_OPTIONAL"] = True
        tc.cache_variables["BUILD_WITH_STD_FILESYSTEM"] = True
        tc.cache_variables["BUILD_C_INTERFACE"] = self.options.c_interface
        tc.cache_variables["BUILD_PYTHON_INTERFACE"] = False
        tc.cache_variables["BUILD_MATLAB_INTERFACE"] = False
        tc.cache_variables["BUILD_OCTAVE_INTERFACE"] = False
        tc.cache_variables["BUILD_TESTS"] = False
        tc.cache_variables["BUILD_EXAMPLES"] = False
        tc.cache_variables["BUILD_BENCHMARKS"] = False
        tc.cache_variables["BUILD_MAROS_MESZAROS_TEST"] = False
        tc.cache_variables["ENABLE_INSTALL"] = True
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "piqp")

        self.cpp_info.components["piqp_header_only"].set_property("cmake_target_name", "piqp::piqp_header_only")
        self.cpp_info.components["piqp_header_only"].defines = ["PIQP_STD_OPTIONAL", "PIQP_STD_FILESYSTEM"]
        self.cpp_info.components["piqp_header_only"].requires = ["eigen::eigen"]
        if self.options.with_blasfeo:
            self.cpp_info.components["piqp_header_only"].requires.append("blasfeo::blasfeo")
            self.cpp_info.components["piqp_header_only"].defines.append("PIQP_HAS_BLASFEO")
        if self.options.with_openmp:
            self.cpp_info.components["piqp_header_only"].requires.append("openmp::openmp")
            self.cpp_info.components["piqp_header_only"].defines.append("PIQP_HAS_OPENMP")

        if not self.options.header_only:
            self.cpp_info.components["core"].set_property("cmake_target_name", "piqp::piqp")
            self.cpp_info.components["core"].libs = ["piqp"]
            self.cpp_info.components["core"].requires = ["piqp_header_only"]
            self.cpp_info.components["core"].defines.append("PIQP_WITH_TEMPLATE_INSTANTIATION")

            if self.options.c_interface:
                self.cpp_info.components["piqp_c"].set_property("cmake_target_name", "piqp::piqp_c")
                self.cpp_info.components["piqp_c"].libs = ["piqpc"]
                self.cpp_info.components["piqp_c"].requires = ["core"]
                if not self.options.shared and stdcpp_library(self):
                    self.cpp_info.components["piqp_c"].system_libs.append(stdcpp_library(self))
