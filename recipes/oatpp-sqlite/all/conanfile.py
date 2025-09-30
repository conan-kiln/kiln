import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc

required_conan_version = ">=2.1"


class OatppSqliteConan(ConanFile):
    name = "oatpp-sqlite"
    description = "SQLite adapter for oatpp ORM."
    license = "Apache-2.0"
    homepage = "https://github.com/oatpp/oatpp-sqlite"
    topics = ("oat++", "oatpp", "sqlite")
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
        self.requires(f"oatpp/{self.version}", transitive_headers=True)
        self.requires("sqlite3/[>=3.45.0 <4]")

    def validate(self):
        check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

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
        self.cpp_info.set_property("cmake_file_name", "oatpp-sqlite")
        self.cpp_info.set_property("cmake_target_name", "oatpp::oatpp-sqlite")

        self.cpp_info.libs = ["oatpp-sqlite"]
        self.cpp_info.libdirs = [f"lib/oatpp-{self._version}"]
        self.cpp_info.includedirs = [f"include/oatpp-{self._version}/oatpp-sqlite"]
        if self.settings.os == "Windows" and self.options.shared:
            self.cpp_info.bindirs = [f"bin/oatpp-{self._version}"]
        else:
            self.cpp_info.bindirs = []
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["pthread"]
