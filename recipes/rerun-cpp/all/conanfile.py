import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class RerunCppConan(ConanFile):
    name = "rerun-cpp"
    description = "Rerun C++ SDK for multimodal data visualization"
    license = "MIT OR Apache-2.0"
    homepage = "https://github.com/rerun-io/rerun"
    topics = ("visualization", "logging", "multimodal", "3d", "computer-vision")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
    }
    default_options = {
        "shared": False,
    }

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires(f"rerun-c/{self.version}", transitive_headers=True, transitive_libs=True)
        self.requires("arrow/[>=18.0]", transitive_headers=True, transitive_libs=True)
        self.requires("loguru/[*]")

    def validate(self):
        check_min_cppstd(self, 17)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.16]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        save(self, "crates/top/rerun_c/CMakeLists.txt", "")
        replace_in_file(self, "rerun_cpp/CMakeLists.txt",
                        "if(NOT TARGET rerun_c)",
                        "find_package(rerun_c REQUIRED)\nif(0)")
        replace_in_file(self, "rerun_cpp/CMakeLists.txt",
                        'if(rerun_sdk_TYPE STREQUAL "STATIC_LIBRARY" AND NOT RERUN_INSTALL_RERUN_C)', "if(0)")
        save(self, "examples/cpp/CMakeLists.txt", "")
        save(self, "tests/cpp/CMakeLists.txt", "")
        save(self, "docs/snippets/CMakeLists.txt", "")
        replace_in_file(self, "CMakeLists.txt",
                        "FetchContent_MakeAvailable(LoguruGitRepo) # defines target 'loguru::loguru'",
                        "find_package(loguru REQUIRED)")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_TESTING"] = False
        tc.cache_variables["RERUN_DOWNLOAD_AND_BUILD_ARROW"] = False
        tc.cache_variables["CMAKE_COMPILE_WARNING_AS_ERROR"] = False
        tc.cache_variables["RERUN_INSTALL_RERUN_C"] = False
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("arrow", "cmake_target_aliases", ["Arrow::arrow_static", "Arrow::arrow_shared"])
        deps.set_property("rerun-c", "cmake_target_name", "rerun_c")
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE*", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "rerun_sdk")
        self.cpp_info.set_property("cmake_target_name", "rerun_sdk")
        self.cpp_info.libs = ["rerun_sdk"]
        if self.settings.os == "Windows" and self.options.shared:
            self.cpp_info.defines = ["RERUN_SDK_COMPILED_AS_SHARED_LIBRARY"]
