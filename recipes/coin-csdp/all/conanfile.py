import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMakeToolchain, CMake
from conan.tools.cmake.cmakedeps.cmakedeps import CMakeDeps
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.4"


class CoinCsdpConan(ConanFile):
    name = "coin-csdp"
    description = ("CSDP is a library of routines that implements a predictor corrector variant "
                   "of the semidefinite programming algorithm of Helmberg, Rendl, Vanderbei, and Wolkowicz.")
    license = "EPL-2.0"
    homepage = "https://github.com/coin-or/Csdp"
    topics = ("optimization", "semidefinite-programming", "coin-or")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "tools": [True, False],
        "with_openmp": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "tools": False,
        "with_openmp": True,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("lapack/latest")
        if self.options.with_openmp:
            self.requires("openmp/system")

    def validate(self):
        if self.settings.compiler == "msvc":
            # includes several sys/ headers
            raise ConanInvalidConfiguration("MSVC is not supported")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # Fix error: implicit declaration of function ‘printf’
        replace_in_file(self, "lib/user_exit.c", "#include <signal.h>", "#include <signal.h>\n#include <stdio.h>")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["CSDP_USE_OPENMP"] = self.options.with_openmp
        tc.cache_variables["CSDP_BUILD_SOLVER"] = self.options.tools
        tc.cache_variables["CSDP_BUILD_THETA"] = self.options.tools
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("cmake_target_aliases", ["csdp"])
        self.cpp_info.libs = ["csdp"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]

        self.runenv_info.prepend_path("MATLABPATH", os.path.join(self.package_folder, "lib", "matlab"))
