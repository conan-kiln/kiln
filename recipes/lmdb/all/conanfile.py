import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.4"


class LmdbConan(ConanFile):
    name = "lmdb"
    description = "Fast and compat memory-mapped key-value database"
    license = "OLDAP-2.8"
    homepage = "https://symas.com/lmdb/"
    topics = ("database", "key-value", "memory-mapped")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "enable_robust_mutex": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "enable_robust_mutex": True,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        self.options.enable_robust_mutex = self.settings.os in ["Linux", "FreeBSD"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["LMDB_ENABLE_ROBUST_MUTEX"] = self.options.enable_robust_mutex
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=os.path.join(self.source_folder, "libraries", "liblmdb"), dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "lmdb")
        self.cpp_info.libs = ["lmdb"]

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["pthread"]
