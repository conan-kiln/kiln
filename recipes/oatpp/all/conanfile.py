import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc, is_msvc_static_runtime

required_conan_version = ">=2.1"


class OatppConan(ConanFile):
    name = "oatpp"
    description = "Modern Web Framework for C++"
    license = "Apache-2.0"
    homepage = "https://github.com/oatpp/oatpp"
    topics = ("oat++", "web-framework")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "build_test_library": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "build_test_library": False,
    }
    implements = ["auto_shared_fpic"]

    @property
    def _version(self):
        return str(self.version).replace(".latest", "")

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if is_msvc(self):
            self.package_type = "static-library"
            del self.options.shared

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        check_min_cppstd(self, 11)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.20 <5]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        replace_in_file(self, "CMakeLists.txt",
                        "cmake_minimum_required(VERSION 3.1 FATAL_ERROR)",
                        "cmake_minimum_required(VERSION 3.5)")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["OATPP_BUILD_TESTS"] = False
        tc.variables["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = True
        tc.variables["OATPP_MSVC_LINK_STATIC_RUNTIME"] = is_msvc_static_runtime(self)
        tc.variables["OATPP_LINK_TEST_LIBRARY"] = self.options.build_test_library
        tc.generate()

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
        self.cpp_info.set_property("cmake_file_name", "oatpp")

        include_dir = f"include/oatpp-{self._version}/oatpp"
        lib_dir =  f"lib/oatpp-{self._version}"

        # oatpp
        self.cpp_info.components["oatpp_"].set_property("cmake_target_name", "oatpp::oatpp")
        self.cpp_info.components["oatpp_"].includedirs = [include_dir]
        self.cpp_info.components["oatpp_"].libdirs = [lib_dir]
        self.cpp_info.components["oatpp_"].libs = ["oatpp"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["oatpp_"].system_libs = ["pthread", "m"]
        elif self.settings.os == "Windows":
            self.cpp_info.components["oatpp_"].system_libs = ["ws2_32", "wsock32"]

        # oatpp-test
        if self.options.build_test_library:
            self.cpp_info.components["oatpp-test"].set_property("cmake_target_name", "oatpp-test::oatpp-test")
            self.cpp_info.components["oatpp-test"].includedirs = [include_dir]
            self.cpp_info.components["oatpp-test"].libdirs = [lib_dir]
            self.cpp_info.components["oatpp-test"].libs = ["oatpp-test"]
            self.cpp_info.components["oatpp-test"].requires = ["oatpp_"]

        # workaround to having all components in the global target
        self.cpp_info.set_property("cmake_target_name", "oatpp::oatpp-test")
