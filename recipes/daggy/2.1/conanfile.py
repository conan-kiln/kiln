import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class DaggyConan(ConanFile):
    name = "daggy"
    description = "Data Aggregation Utility and C/C++ developer library for data streams catching"
    license = "MIT"
    homepage = "https://github.com/synacker/daggy"
    topics = ("streaming", "qt", "monitoring", "process", "stream-processing", "extensible",
              "serverless-framework", "aggregation", "ssh2", "cross-platform", "ssh-client")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_ssh2": [True, False],
        "with_yaml": [True, False],
        "with_console": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_ssh2": True,
        "with_yaml": True,
        "with_console": False,
    }
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        # Qt is used in the public headers
        self.requires("qt/[>=6.7 <7]", transitive_headers=True, transitive_libs=True)
        self.requires("kainjow-mustache/4.1")
        if self.options.with_yaml:
            self.requires("yaml-cpp/[>=0.8.0 <1]")
        if self.options.with_ssh2:
            self.requires("libssh2/[^1.11.0]")

    def validate(self):
        check_min_cppstd(self, 17)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.27 <5]")
        self.tool_requires("qt/<host_version>")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["SSH2_SUPPORT"] = self.options.with_ssh2
        tc.cache_variables["YAML_SUPPORT"] = self.options.with_yaml
        tc.cache_variables["CONSOLE"] = self.options.with_console
        tc.cache_variables["PACKAGE_DEPS"] = False
        tc.cache_variables["VERSION"] = self.version
        tc.cache_variables["CONAN_BUILD"] = True
        tc.cache_variables["BUILD_TESTING"] = False
        # Set version without git
        tc.cache_variables["CMAKE_DISABLE_FIND_PACKAGE_Git"] = True
        tc.cache_variables["VERSION"] = f"{self.version}.0"
        if self.options.shared:
            tc.cache_variables["CMAKE_C_VISIBILITY_PRESET"] = "hidden"
            tc.cache_variables["CMAKE_CXX_VISIBILITY_PRESET"] = "hidden"
            tc.cache_variables["CMAKE_VISIBILITY_INLINES_HIDDEN"] = 1
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder="src")
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "DaggyCore")
        self.cpp_info.set_property("cmake_target_name", "daggy::DaggyCore")
        self.cpp_info.libs = ["DaggyCore"]
        self.cpp_info.requires = ["qt::qtCore", "qt::qtNetwork", "kainjow-mustache::kainjow-mustache"]
        if self.options.with_yaml:
            self.cpp_info.requires.append("yaml-cpp::yaml-cpp")
        if self.options.with_ssh2:
            self.cpp_info.requires.append("libssh2::libssh2")
