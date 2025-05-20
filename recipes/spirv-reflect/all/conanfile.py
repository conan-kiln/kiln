import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class SpirvReflectConan(ConanFile):
    name = "spirv-reflect"
    description = ("SPIRV-Reflect is a lightweight library that provides a C/C++ reflection API "
                   "for SPIR-V shader bytecode in Vulkan applications.")
    license = "Apache-2.0"
    topics = ("spirv", "spirv-v", "vulkan", "opengl", "opencl", "khronos")
    homepage = "https://github.com/KhronosGroup/SPIRV-Reflect"
    url = "https://github.com/conan-io/conan-center-index"
    package_type = "static-library"
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires(f"spirv-headers/{self.version}", transitive_headers=True)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.16 <5]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        replace_in_file(self, "CMakeLists.txt", "set(CMAKE_CXX_STANDARD 14)", "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["SPIRV_REFLECT_STATIC_LIB"] = True
        tc.cache_variables["SPIRV_REFLECT_EXAMPLES"] = False
        tc.cache_variables["SPIRV_REFLECT_BUILD_TESTS"] = False
        if Version(self.version) < "1.3.296.0":
            tc.cache_variables["CMAKE_POLICY_VERSION_MINIMUM"] = "3.16" # CMake 4 support
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        if Version(self.version) < "1.4.313.0":
            copy(self, "spirv_reflect.h", self.source_folder, os.path.join(self.package_folder, "include"))

    def package_info(self):
        # No official CMake config is exported - using a naming scheme similar to other SPIRV packages instead.
        self.cpp_info.set_property("cmake_file_name", "SPIRV-Reflect")
        self.cpp_info.set_property("cmake_target_name", "spirv-reflect-static")
        self.cpp_info.libs = ["spirv-reflect-static"]
        self.cpp_info.defines.append("SPIRV_REFLECT_USE_SYSTEM_SPIRV_H")
