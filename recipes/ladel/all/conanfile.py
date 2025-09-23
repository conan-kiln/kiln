import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class LADELConan(ConanFile):
    name = "ladel"
    description = "LADEL: Quasidefinite LDL factorization package with (symmetric) row/column adds and deletes"
    license = "LGPL-3.0-or-later"
    homepage = "https://github.com/kul-optec/LADEL"
    topics = ("LDL", "LDLT", "linear-algebra", "sparse-matrix", "factorization")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "precision_single": [True, False],
        "use_64bit_indices": [True, False],
        "use_simple_col_counts": [True, False],
        "with_amd": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "precision_single": False,
        "use_64bit_indices": True,
        "use_simple_col_counts": False,
        "with_amd": True,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_amd:
            self.requires("suitesparse-amd/[^3.3]")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.23]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        rmdir(self, "thirdparty")
        replace_in_file(self, "LADEL/CMakeLists.txt",
                        "add_subdirectory(../thirdparty/SuiteSparse SuiteSparse EXCLUDE_FROM_ALL)",
                        "find_package(AMD REQUIRED)")
        replace_in_file(self, "LADEL/cmake/Install.cmake", "LADEL_USE_AMD", "FALSE")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["LADEL_USE_AMD"] = self.options.with_amd
        tc.cache_variables["LADEL_SIMPLE_COL_COUNTS"] = self.options.use_simple_col_counts
        tc.cache_variables["LADEL_64BIT_INDICES"] = self.options.use_64bit_indices
        tc.cache_variables["LADEL_SINGLE_PRECISION"] = self.options.precision_single
        tc.cache_variables["LADEL_WITH_MEX"] = False
        tc.cache_variables["BUILD_TESTING"] = False
        tc.cache_variables["LADEL_WITH_COVERAGE"] = False
        tc.cache_variables["LADEL_FORCE_TEST_DISCOVERY"] = False
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("suitesparse-amd", "cmake_target_name", "ladel_amd")
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
        self.cpp_info.set_property("cmake_file_name", "LADEL")
        self.cpp_info.set_property("cmake_target_name", "LADEL::ladel")
        self.cpp_info.libs = ["ladel"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]
        if self.options.use_simple_col_counts:
            self.cpp_info.defines.append("LADEL_SIMPLE_COL_COUNTS")
        if self.options.use_64bit_indices:
            self.cpp_info.defines.append("LADEL_64BIT_INDICES")
        if not self.options.precision_single:
            self.cpp_info.defines.append("LADEL_SINGLE_PRECISION")
        if self.options.with_amd:
            self.cpp_info.requires.append("suitesparse-amd::suitesparse-amd")
            self.cpp_info.defines.append("LADEL_USE_AMD")
