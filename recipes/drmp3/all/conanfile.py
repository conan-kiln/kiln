import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.4"


class Drmp3Conan(ConanFile):
    name = "drmp3"
    description = "MP3 audio decoder."
    homepage = "https://github.com/mackron/dr_libs"
    topics = ("audio", "mp3", "sound")
    license = ("Unlicense", "MIT-0")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "no_simd": [True, False],
        "no_stdio": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "no_simd": False,
        "no_stdio": False,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    exports_sources = ["CMakeLists.txt", "dr_mp3.c"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["DRMP3_SRC_DIR"] = self.source_folder.replace("\\", "/")
        tc.variables["NO_SIMD"] = self.options.no_simd
        tc.variables["NO_STDIO"] = self.options.no_stdio
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder="..")
        cmake.build()

    def package(self):
        copy(self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["dr_mp3"]
        if self.options.shared:
            self.cpp_info.defines.append("DRMP3_DLL")
        if self.options.no_simd:
            self.cpp_info.defines.append("DR_MP3_NO_SIMD")
        if self.options.no_stdio:
            self.cpp_info.defines.append("DR_MP3_NO_STDIO")
