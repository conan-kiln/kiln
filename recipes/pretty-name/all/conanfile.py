import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class PrettyNameConan(ConanFile):
    name = "pretty-name"
    description = "An easy and consistent way how to get type names in C++"
    license = "MIT"
    homepage = "https://github.com/Rechip/pretty-name"
    topics = ("cpp", "typename", "header-only")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    @property
    def _min_cppstd(self):
        return 14

    @property
    def _minimum_compilers_version(self):
        return {
            "gcc": "5",
            "clang": "5",
            "apple-clang": "5.1",
        }

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def validate(self):
        check_min_cppstd(self, self._min_cppstd)
        minimum_version = self._minimum_compilers_version.get(str(self.settings.compiler), False)
        if not minimum_version:
            self.output.warning("pretty-name requires C++14. Your compiler is unknown. Assuming it supports C++14.")
        elif Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration("pretty-name requires C++14, which your compiler does not support.")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE",
             dst=os.path.join(self.package_folder, "licenses"),
             src=self.source_folder)
        copy(self, "*",
             dst=os.path.join(self.package_folder, "include"),
             src=os.path.join(self.source_folder, "include"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []

        self.cpp_info.set_property("cmake_file_name", "pretty-name")
        self.cpp_info.set_property("cmake_target_name", "pretty-name::pretty-name")
