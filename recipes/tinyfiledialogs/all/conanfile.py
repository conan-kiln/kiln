import os
from pathlib import Path

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class TinyfiledialogsConan(ConanFile):
    name = "tinyfiledialogs"
    description = "Highly portable and cross-platform dialogs for native inputbox, passwordbox, colorpicker and more"
    license = "Zlib"
    homepage = "https://sourceforge.net/projects/tinyfiledialogs"
    topics = ("file-picker", "color-picker", "gui")
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
    languages = ["C"]

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        for file in ["tinyfiledialogs.c", "tinyfiledialogs.h"]:
            download(self, **self.conan_data["sources"][self.version][file], filename=file)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def _extract_license(self):
        content = Path(self.source_folder, "tinyfiledialogs.c").read_text()
        return content.split("- License -", 1)[1].split("\n\n", 1)[0].strip()

    def package(self):
        save(self, os.path.join(self.package_folder, "licenses", "LICENSE"), self._extract_license())
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["tinyfiledialogs"]
        self.cpp_info.includedirs.append("include/tinyfiledialogs")
