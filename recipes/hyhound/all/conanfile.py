import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class HyhoundConan(ConanFile):
    name = "hyhound"
    description = "Hyperbolic Householder transformations for Up- and Downdating Cholesky factorizations"
    license = "LGPL-3.0-only"
    homepage = "https://github.com/kul-optec/hyhound"
    topics = ("linear-algebra", "cholesky", "matrix-factorization", "optimization", "scientific-computing")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "float": [True, False],
        "double": [True, False],
        "index_type": ["int", "long long"],
        "enable_ocp": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "float": True,
        "double": True,
        "index_type": "long long",
        "enable_ocp": True,
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("guanaqo/[^1.0, include_prerelease]", transitive_headers=True, transitive_libs=True)
        if self.options.enable_ocp:
            self.requires("eigen/[>=3.3 <6]", transitive_headers=True)

    def validate(self):
        check_min_cppstd(self, 17)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.24]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        real_type = []
        if self.options.float:
            real_type.append("float")
        if self.options.double:
            real_type.append("double")
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_TESTING"] = False
        tc.cache_variables["HYHOUND_WITH_TESTS"] = False
        tc.cache_variables["HYHOUND_WITH_BENCHMARKS"] = False
        tc.cache_variables["HYHOUND_DENSE_REAL_TYPE"] = ";".join(real_type)
        tc.cache_variables["HYHOUND_DENSE_INDEX_TYPE"] = self.options.index_type
        tc.cache_variables["HYHOUND_WITH_OCP"] = self.options.enable_ocp
        tc.cache_variables["HYHOUND_WARNINGS_AS_ERRORS"] = False
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

    @property
    def _lib_suffix(self):
        return {
            "Debug": "_d",
            "RelWithDebInfo": "_rd",
            "MinSizeRel": "_rs",
        }.get(str(self.settings.build_type), "")

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "hyhound")
        self.cpp_info.components["core"].set_property("cmake_target_name", "hyhound::hyhound")
        self.cpp_info.components["core"].libs = ["hyhound" + self._lib_suffix]
        self.cpp_info.components["core"].requires = ["guanaqo::guanaqo"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["core"].system_libs = ["m", "pthread"]

        if self.options.enable_ocp:
            self.cpp_info.components["ocp"].set_property("cmake_target_name", "hyhound::ocp")
            self.cpp_info.components["ocp"].libs = ["hyhound-ocp" + self._lib_suffix]
            self.cpp_info.components["ocp"].requires = ["core", "eigen::eigen"]
