import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class UcxxConan(ConanFile):
    name = "ucxx"
    description = "C++ interface for the UCX communication framework"
    license = "BSD-3-Clause"
    homepage = "https://github.com/rapidsai/ucxx"
    topics = ("ucx", "communication", "networking", "hpc", "rapids")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_rmm": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_rmm": False,
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("openucx/[^1]", transitive_headers=True, transitive_libs=True)
        if self.options.with_rmm:
            self.requires("rmm/[^25.0]")

    def validate(self):
        check_min_cppstd(self, 17)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.26.4]")
        self.tool_requires("rapids-cmake/25.08.00")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        save(self, "cmake/RAPIDS.cmake", "find_package(rapids-cmake REQUIRED)")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_TESTS"] = False
        tc.cache_variables["BUILD_BENCHMARKS"] = False
        tc.cache_variables["BUILD_EXAMPLES"] = False
        tc.cache_variables["UCXX_ENABLE_RMM"] = self.options.with_rmm
        tc.cache_variables["FETCHCONTENT_FULLY_DISCONNECTED"] = True
        tc.cache_variables["CMAKE_PREFIX_PATH"] = self.generators_folder.replace("\\", "/")
        tc.generate()

        deps = CMakeDeps(self)
        deps.build_context_activated.append("rapids-cmake")
        deps.build_context_build_modules.append("rapids-cmake")
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder="cpp")
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "ucxx")
        self.cpp_info.set_property("cmake_target_name", "ucxx::ucxx")
        self.cpp_info.set_property("cmake_additional_variables_prefixes", ["UCXX"])
        self.cpp_info.libs = ["ucxx"]
        if self.options.with_rmm:
            self.cpp_info.defines = ["UCXX_ENABLE_RMM"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["pthread", "m"]
