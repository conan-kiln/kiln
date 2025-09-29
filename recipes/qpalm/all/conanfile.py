import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd, check_min_cstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class QpalmConan(ConanFile):
    name = "qpalm"
    description = "Proximal Augmented Lagrangian method for Quadratic Programs"
    license = "LGPL-3.0-or-later"
    homepage = "https://github.com/kul-optec/QPALM"
    topics = ("optimization", "quadratic-program", "qp", "alm")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "cxx": [True, False],
        "with_ladel": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "cxx": True,
        "with_ladel": True,
    }
    implements = ["auto_shared_fpic"]

    def configure(self):
        if not self.options.cxx:
            self.languages = ["C"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_ladel:
            self.requires("ladel/[>=0.0.4 <1]", transitive_headers=True)
        if self.options.cxx:
            self.requires("eigen/[>=3.3 <6]", transitive_headers=True)

    def validate(self):
        if self.settings.get_safe("compiler.cstd"):
            check_min_cstd(self, 11)
        if self.options.cxx:
            check_min_cppstd(self, 17)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.23]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        replace_in_file(self, "QPALM/CMakeLists.txt", "add_subdirectory(../LADEL/LADEL LADEL EXCLUDE_FROM_ALL)", "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["QPALM_WITH_CXX"] = self.options.cxx
        tc.cache_variables["QPALM_WITH_FORTRAN"] = False
        tc.cache_variables["QPALM_WITH_PYTHON"] = False
        tc.cache_variables["QPALM_WITH_JULIA"] = False
        tc.cache_variables["QPALM_WITH_MEX"] = False
        tc.cache_variables["QPALM_WITH_MTX"] = False
        tc.cache_variables["QPALM_WITH_QPS"] = False
        tc.cache_variables["QPALM_WITH_EXAMPLES"] = False
        tc.cache_variables["QPALM_WARNINGS_AS_ERRORS"] = False
        tc.cache_variables["BUILD_TESTING"] = False
        tc.cache_variables["QPALM_DOXYGEN"] = "-NOTFOUND"
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        replace_in_file(self, os.path.join(self.source_folder, "QPALM/CMakeLists.txt"),
                        "find_package(LADEL QUIET)",
                        "find_package(LADEL REQUIRED)" if self.options.with_ladel else "")
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    @property
    def _lib_suffix(self):
        if self.settings.build_type == "Debug":
            return "d"
        return ""

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "QPALM")

        self.cpp_info.components["core"].set_property("cmake_target_name", "QPALM::qpalm")
        self.cpp_info.components["core"].libs = [f"qpalm{self._lib_suffix}"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["core"].system_libs = ["m"]
        v = Version(self.version)
        self.cpp_info.components["core"].defines = [
            f'QPALM_VERSION_STR="{self.version}"',
            f"QPALM_VERSION_MAJOR={v.major}",
            f"QPALM_VERSION_MINOR={v.minor}",
            f"QPALM_VERSION_PATCH={v.patch}",
        ]
        if self.options.get_safe("nonconvex", True):
            self.cpp_info.components["core"].defines.append("QPALM_NONCONVEX")
        if self.options.get_safe("timing", True):
            self.cpp_info.components["core"].defines.append("QPALM_TIMING")
        if self.options.get_safe("printing", True):
            self.cpp_info.components["core"].defines.append("QPALM_PRINTING")
        if self.options.with_ladel:
            self.cpp_info.components["core"].defines.append("QPALM_USE_LADEL")
            self.cpp_info.components["core"].requires.append("ladel::ladel")

        if self.options.cxx:
            self.cpp_info.components["qpalm_cxx"].set_property("cmake_target_name", "QPALM::qpalm_cxx")
            self.cpp_info.components["qpalm_cxx"].set_property("cmake_additional_variables_prefixes", ["QPALM_cxx"])
            self.cpp_info.components["qpalm_cxx"].libs = [f"qpalm_cxx{self._lib_suffix}"]
            self.cpp_info.components["qpalm_cxx"].requires = ["core"]
            if self.options.cxx:
                self.cpp_info.components["qpalm_cxx"].requires.append("eigen::eigen")
