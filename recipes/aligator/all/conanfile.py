import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class AligatorConan(ConanFile):
    name = "aligator"
    description = "A versatile and efficient C++ library for real-time constrained trajectory optimization"
    license = "BSD-2-Clause"
    homepage = "https://github.com/Simple-Robotics/aligator"
    topics = ("trajectory-optimization", "robotics", "optimal-control", "augmented-lagrangian")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "enable_template_instantiation": [True, False],
        "with_crocoddyl": [True, False],
        "with_pinocchio": [True, False],
        "with_cholmod": [True, False],
        "with_openmp": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "enable_template_instantiation": False,
        "with_crocoddyl": False,
        "with_pinocchio": False,
        "with_cholmod": False,
        "with_openmp": True,
        "boost/*:with_filesystem": True,
        "pinocchio/*:with_coal": True,
    }
    implements = ["auto_shared_fpic"]

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if self.options.with_crocoddyl:
            self.options.with_pinocchio.value = True

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_pinocchio:
            self.requires("pinocchio/[^3.4.0]", transitive_headers=True, transitive_libs=True)
        if self.options.with_crocoddyl:
            self.requires("crocoddyl/[^3.0.1]", transitive_headers=True, transitive_libs=True)
        if self.options.with_cholmod:
            self.requires("suitesparse-cholmod/[^5]", transitive_headers=True, transitive_libs=True)
        if self.options.with_openmp:
            self.requires("openmp/system")
        self.requires("eigen/[>=3.3 <6]", transitive_headers=True)
        self.requires("fmt/[>=10 <12]", transitive_headers=True, transitive_libs=True)
        self.requires("boost/[^1.71]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        check_min_cppstd(self, 17)
        if self.options.with_pinocchio and not self.dependencies["pinocchio"].options.with_coal:
            raise ConanInvalidConfiguration("pinocchio/*:with_coal=True is required")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.22]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        replace_in_file(self, "CMakeLists.txt", "${JRL_CMAKE_MODULES}/find-external", "# ")
        # Breaks with CMakeDeps
        replace_in_file(self, "CMakeLists.txt", "PKG_CONFIG_APPEND_BOOST_LIBS(", "# ")
        replace_in_file(self, "include/aligator/core/manifold-base.hpp",
                        '#include "aligator/fwd.hpp"',
                        '#include "aligator/fwd.hpp"\n\n#include<cassert>')

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_TESTING"] = False
        tc.cache_variables["BUILD_EXAMPLES"] = False
        tc.cache_variables["BUILD_BENCHMARKS"] = False
        tc.cache_variables["BUILD_PYTHON_INTERFACE"] = False
        tc.cache_variables["GENERATE_PYTHON_STUBS"] = False
        tc.cache_variables["BUILD_WITH_PINOCCHIO_SUPPORT"] = self.options.with_pinocchio
        tc.cache_variables["BUILD_CROCODDYL_COMPAT"] = self.options.with_crocoddyl
        tc.cache_variables["BUILD_WITH_OPENMP_SUPPORT"] = self.options.with_openmp
        tc.cache_variables["BUILD_WITH_CHOLMOD_SUPPORT"] = self.options.with_cholmod
        tc.cache_variables["ENABLE_TEMPLATE_INSTANTIATION"] = self.options.enable_template_instantiation
        tc.cache_variables["BUILD_WITH_VERSION_SUFFIX"] = True
        tc.cache_variables["INSTALL_DOCUMENTATION"] = False
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("suitesparse-cholmod", "cmake_target_name", "CHOLMOD::CHOLMOD")
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        if self.options.enable_template_instantiation:
            self._utils.limit_build_jobs(self, gb_mem_per_job=3)
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "aligator")
        self.cpp_info.set_property("pkg_config_name", "aligator")

        self.cpp_info.components["aligator_"].set_property("cmake_target_name", "aligator::aligator")
        self.cpp_info.components["aligator_"].libs = ["aligator"]
        if self.options.enable_template_instantiation:
            self.cpp_info.components["aligator_"].defines.append("ALIGATOR_ENABLE_TEMPLATE_INSTANTIATION")
        self.cpp_info.components["aligator_"].requires = ["eigen::eigen", "fmt::fmt", "boost::filesystem"]
        if self.options.with_pinocchio:
            self.cpp_info.components["aligator_"].requires.append("pinocchio::pinocchio_collision")
            self.cpp_info.components["aligator_"].defines.append("ALIGATOR_WITH_PINOCCHIO")
        if self.options.with_cholmod:
            self.cpp_info.components["aligator_"].requires.append("suitesparse-cholmod::suitesparse-cholmod")
            self.cpp_info.components["aligator_"].defines.append("ALIGATOR_WITH_CHOLMOD")
        if self.options.with_openmp:
            self.cpp_info.components["aligator_"].requires.append("openmp::openmp")
            self.cpp_info.components["aligator_"].defines.append("ALIGATOR_MULTITHREADING")
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["aligator_"].system_libs = ["m", "pthread", "dl"]

        if self.options.with_crocoddyl:
            self.cpp_info.components["croc_compat"].set_property("cmake_target_name", "aligator::croc_compat")
            self.cpp_info.components["croc_compat"].libs = ["aligator_croc_compat"]
            self.cpp_info.components["croc_compat"].defines = ["ALIGATOR_WITH_CROCODDYL_COMPAT"]
            self.cpp_info.components["croc_compat"].requires = ["aligator_", "crocoddyl::crocoddyl"]
