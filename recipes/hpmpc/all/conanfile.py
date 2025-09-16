import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class HpmpcConan(ConanFile):
    name = "hpmpc"
    description = "HPMPC: Library for High-Performance implementation of solvers for MPC"
    license = "LGPL-2.1-or-later"
    homepage = "https://github.com/giaf/hpmpc"
    topics = ("mpc", "optimization", "control", "linear-algebra", "riccati")
    package_type = "static-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "fPIC": [True, False],
        "target": ["x64_avx2", "x64_avx", "x64_sse3", "cortex_a57", "cortex_a15", "cortex_a9", "cortex_a7", "c99_4x4"],
    }
    default_options = {
        "fPIC": True,
        "target": "c99_4x4",
    }
    languages = ["C"]

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if self.settings.arch == "x86_64":
            self.options.target = "x64_avx2"
        elif self.settings.arch in ["armv8", "armv8.3"]:
            self.options.target = "cortex_a57"
        elif self.settings.arch in ["armv7", "armv7hf"]:
            self.options.target = "cortex_a15"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("blasfeo/[>=0.1 <1]", transitive_headers=True, transitive_libs=True)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        rmdir(self, "blas")
        rmdir(self, "reference_code")
        replace_in_file(self, "CMakeLists.txt",
                        "cmake_minimum_required(VERSION 2.8.11)",
                        "cmake_minimum_required(VERSION 3.5)")
        replace_in_file(self, "CMakeLists.txt", "set(PREFIX /usr)", "")
        replace_in_file(self, "CMakeLists.txt", "set(TARGET C99_4X4)", "")
        replace_in_file(self, "CMakeLists.txt", " -fPIC", "")
        replace_in_file(self, "CMakeLists.txt",
                        '-I${BLASFEO_PATH}/include")',
                        '")\nfind_package(blasfeo REQUIRED)\n')

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["TARGET"] = str(self.options.target).upper()
        tc.preprocessor_definitions[f"TARGET_{str(self.options.target).upper()}"] = ""
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE*", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "hpmpc")
        self.cpp_info.set_property("cmake_target_name", "hpmpc")
        self.cpp_info.set_property("pkg_config_name", "hpmpc")
        self.cpp_info.libs = ["hpmpc"]
        self.cpp_info.defines.append(f"TARGET_{str(self.options.target).upper()}")
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]
