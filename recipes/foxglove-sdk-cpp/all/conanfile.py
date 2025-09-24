import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class FoxgloveSdkCppConan(ConanFile):
    name = "foxglove-sdk-cpp"
    description = "C++ libraries and schemas for Foxglove"
    license = "MIT"
    homepage = "https://github.com/foxglove/foxglove-sdk"
    topics = ("visualization", "robotics", "data-visualization", "ros", "ros2", "mcap")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
    }
    default_options = {
        "shared": False,
    }

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, self.export_sources_folder)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires(f"foxglove-sdk-c/{self.version}", transitive_headers=True, transitive_libs=True)
        self.requires("websocketpp/[>=0.8 <1]")
        self.requires("asio/[^1.31]")
        self.requires("nlohmann_json/[^3]")
        self.requires("tl-expected/[^1.2.0]", transitive_headers=True)

    def validate(self):
        check_min_cppstd(self, 17)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.25]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        copy(self, "CMakeLists.txt", self.export_sources_folder, os.path.join(self.source_folder, "cpp"))
        os.unlink("cpp/foxglove/include/foxglove/expected.hpp")
        replace_in_file(self, "cpp/foxglove/include/foxglove/error.hpp",
                        '#include "expected.hpp"',
                        "#include <tl/expected.hpp>")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["STRICT"] = False
        tc.cache_variables["BUILD_TESTING"] = False
        tc.cache_variables["FETCHCONTENT_FULLY_DISCONNECTED"] = True
        tc.generate()

        deps = CMakeDeps(self)
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
        self.cpp_info.libs = ["foxglove_cpp"]
