import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd, stdcpp_library
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc_static_runtime, is_msvc
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class GcgConan(ConanFile):
    name = "gcg"
    description = "GCG is a generic decomposition solver for mixed-integer linear programs (MILPs)"
    license = "Apache-2.0"
    homepage = "https://github.com/scipopt/gcg"
    topics = ("optimization", "mixed-integer-programming", "decomposition")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "tools": [True, False],
        "threading": ["none", "omp"],
        "sym": ["none", "bliss", "sbliss", "nauty", "snauty"],
        "with_gmp": [True, False],
        "with_gsl": [True, False],
        "with_cliquer": [True, False],
        "with_cplex": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "tools": False,
        "threading": "omp",
        "sym": "snauty",
        "with_gmp": True,
        "with_gsl": True,
        "with_cliquer": True,
        "with_cplex": False,
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("scip/[*]", transitive_headers=True, transitive_libs=True)
        self.requires("zlib-ng/[^2.0]")
        if self.options.with_gmp:
            self.requires("gmp/[^6.3.0]")
        if self.options.with_gsl:
            self.requires("gsl/[^2.7]", transitive_headers=True, transitive_libs=True)
        if self.options.with_cliquer:
            self.requires("cliquer/[^1.23]")
        if self.options.with_cplex:
            self.requires("cplex/[*]")

        # Symmetry computation dependencies
        if self.options.sym in ["bliss", "sbliss"]:
            self.requires("bliss/[>=0.77 <1]")
        elif self.options.sym in ["nauty", "snauty"]:
            self.requires("nauty/[^2.9.1]")
        if self.options.sym in ["sbliss", "snauty"]:
            self.requires("sassy/[*]")

        # Threading dependencies
        if self.options.threading == "omp":
            self.requires("openmp/system")

    def validate(self):
        check_min_cppstd(self, 14)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        if Version(self.version) <= "3.7.2":
            replace_in_file(self, "CMakeLists.txt",
                            "cmake_minimum_required(VERSION 3.3)",
                            "cmake_minimum_required(VERSION 3.5)")
        replace_in_file(self, "CMakeLists.txt", " ${NAUTY_DEFINITIONS}", "")
        replace_in_file(self, "src/symmetry/automorphism_nauty.cpp", '#include "nauty/', '#include "')
        replace_in_file(self, "src/symmetry/automorphism_nauty.cpp", "TLS_ATTR", "thread_local")
        replace_in_file(self, "src/CMakeLists.txt", "INSTALL_RPATH_USE_LINK_PATH TRUE", "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_TESTING"] = False
        tc.cache_variables["SHARED"] = self.options.shared
        tc.cache_variables["OPENMP"] = self.options.threading == "omp"
        tc.cache_variables["GSL"] = self.options.with_gsl
        tc.cache_variables["GMP"] = self.options.with_gmp
        tc.cache_variables["STATIC_GMP"] = self.options.with_gmp and not self.dependencies["gmp"].options.shared
        tc.cache_variables["CLIQUER"] = self.options.with_cliquer
        tc.cache_variables["CPLEX"] = self.options.with_cplex
        tc.cache_variables["HMETIS"] = False  # TODO
        tc.cache_variables["SYM"] = self.options.sym
        tc.cache_variables["MT"] = is_msvc_static_runtime(self)
        tc.cache_variables["GCG_DEV_BUILD"] = False
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("bliss", "cmake_file_name", "Bliss")
        deps.set_property("bliss", "cmake_target_name", "Bliss::libbliss")
        deps.set_property("cliquer", "cmake_file_name", "CLIQUER")
        deps.set_property("cplex", "cmake_file_name", "CPLEX")
        deps.set_property("gmp", "cmake_file_name", "GMP")
        deps.set_property("gsl", "cmake_file_name", "GSL")
        deps.set_property("nauty", "cmake_file_name", "NAUTY")
        deps.generate()

    def _patch_sources(self):
        if not self.options.tools:
            # Disable gcg executable installation if tools=False
            replace_in_file(self, os.path.join(self.source_folder, "src/CMakeLists.txt"),
                            "install(TARGETS gcg libgcg",
                            "install(TARGETS libgcg")

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        if self.options.tools:
            cmake.build()
        else:
            cmake.build(target="libgcg")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "gcg")
        self.cpp_info.set_property("cmake_additional_variables_prefixes", ["GCG"])
        self.cpp_info.set_property("cmake_target_aliases", ["libgcg"])
        self.cpp_info.libs = ["libgcg" if is_msvc(self) else "gcg"]
        if not self.options.shared:
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.system_libs = ["m", "pthread", "dl"]
            if stdcpp_library(self):
                self.cpp_info.system_libs.append(stdcpp_library(self))
