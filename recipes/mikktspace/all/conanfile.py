import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.4"


class MikkTSpaceConan(ConanFile):
    name = "mikktspace"
    description = "A common standard for tangent space used in baking tools to produce normal maps."
    license = "Zlib"
    homepage = "https://github.com/mmikk/MikkTSpace"
    topics = ("tangent", "space", "normal")
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
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    @property
    def _extracted_license(self):
        content_lines = open(os.path.join(self.source_folder, "mikktspace.h")).readlines()
        license_content = []
        for i in range(4, 21):
            license_content.append(content_lines[i][4:-1])
        return "\n".join(license_content)

    def package(self):
        save(self, os.path.join(self.package_folder, "licenses", "LICENSE"), self._extracted_license)
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["mikktspace"]
        if not self.options.shared and self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]
