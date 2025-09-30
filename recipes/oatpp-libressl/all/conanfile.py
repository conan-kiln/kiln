import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc

required_conan_version = ">=2.1"


class OatppLibresslConan(ConanFile):
    name = "oatpp-libressl"
    license = "Apache-2.0"
    homepage = "https://github.com/oatpp/oatpp-libressl"
    description = "oat++ libressl library"
    topics = ("oat++", "oatpp", "libressl")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
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

    def requirements(self):
        # There's a 1 to 1 match between versions of oatpp and oatpp-libressl
        # oatpp-libressl/oatpp-libressl/Config.hpp:28 and 30 contain includes to these libraries
        self.requires(f"oatpp/{self.version}", transitive_headers=True)
        self.requires("libressl/[^3.5.3]", transitive_headers=True)

    def validate(self):
        check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        replace_in_file(self, "CMakeLists.txt",
                        "cmake_minimum_required(VERSION 3.1 FATAL_ERROR)",
                        "cmake_minimum_required(VERSION 3.5)")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["OATPP_BUILD_TESTS"] = False
        tc.variables["OATPP_MODULES_LOCATION"] = "INSTALLED"
        tc.generate()
        deps = CMakeDeps(self)
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
        self.cpp_info.set_property("cmake_file_name", "oatpp-libressl")
        self.cpp_info.set_property("cmake_target_name", "oatpp::oatpp-libressl")

        self.cpp_info.libs = ["oatpp-libressl"]
        self.cpp_info.libdirs = [f"lib/oatpp-{self._version}"]
        self.cpp_info.includedirs = [f"include/oatpp-{self._version}/oatpp-libressl"]
        if self.settings.os == "Windows" and self.options.shared:
            self.cpp_info.bindirs = [f"bin/oatpp-{self._version}"]
        else:
            self.cpp_info.bindirs = []
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m", "pthread"]
