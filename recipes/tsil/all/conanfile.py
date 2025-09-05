import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc

required_conan_version = ">=2.4"


class TsilConan(ConanFile):
    name = "tsil"
    license = "GPL-2.0-or-later"
    homepage = "https://www.niu.edu/spmartin/TSIL/"
    description = "Two-loop Self-energy Integral Library"
    topics = ("high-energy", "physics", "hep", "two-loop", "integrals")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "size": ["long", "double"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "size": "long",
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    exports_sources = "CMakeLists.txt"

    @property
    def _tsil_size(self):
        return "TSIL_SIZE_DOUBLE" if self.options.size == "double" else "TSIL_SIZE_LONG"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        if is_msvc(self):
            raise ConanInvalidConfiguration(f"TSIL does not support {self.settings.compiler}")

    def source(self):
        get(self, **self.conan_data["sources"][self.version],
            destination=self.source_folder, strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["TSIL_SRC_DIR"] = self.source_folder.replace("\\", "/")
        tc.variables["TSIL_SIZE"] = self.options.size
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder="..")
        cmake.build()

    def package(self):
        copy(self, "LICENSE.txt", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["tsil"]
        self.cpp_info.defines.append(self._tsil_size)
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("m")
