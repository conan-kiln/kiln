import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd, stdcpp_library
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class ClRngConan(ConanFile):
    name = "clrng"
    description = "clRNG is a library for uniform random number generation in OpenCL."
    license = "Apache-2.0"
    homepage = "https://github.com/clMathLibraries/clRNG"
    topics = ("opencl", "clmath", "rng", "random")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "opencl_version": ["2.0", "1.2", "1.1"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "opencl_version": "2.0",
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("opencl-icd-loader/[*]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        check_min_cppstd(self, 11)

    def build_requirements(self):
        self.tool_requires("cmake/[<4]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_TEST"] = False
        tc.cache_variables["BUILD_BENCHMARKS"] = False
        tc.cache_variables["BUILD_EXAMPLES"] = False
        tc.cache_variables["BUILD_SAMPLES"] = False
        tc.cache_variables["BUILD_CLIENT"] = False
        tc.cache_variables["USE_SYSTEM_CL2HPP"] = True
        tc.cache_variables["OPENCL_VERSION"] = str(self.options.opencl_version)
        tc.cache_variables["OPENCL_LIBRARIES"] = "OpenCL::OpenCL"
        tc.cache_variables["SUFFIX_LIB"] = ""
        tc.cache_variables["SUFFIX_BIN"] = ""
        opencl_version = Version(self.options.opencl_version.value)
        tc.preprocessor_definitions["CL_TARGET_OPENCL_VERSION"] = str(int(opencl_version.major.value) * 100 + int(opencl_version.minor.value) * 10)
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0077"] = "NEW"
        if self.settings.compiler != "msvc":
            tc.extra_cflags.append("-Wno-expansion-to-defined")
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder="src")
        cmake.build()

    def package(self):
        copy(self, "LICENSE*", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "clRNG")
        self.cpp_info.set_property("cmake_target_name", "clRNG")
        self.cpp_info.set_property("pkg_config_name", "clRNG")
        self.cpp_info.libs = ["clRNG"]
        if not self.options.shared:
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.system_libs = ["m"]
            if stdcpp_library(self):
                self.cpp_info.system_libs.append(stdcpp_library(self))
