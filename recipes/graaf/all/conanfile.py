import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class GraafConan(ConanFile):
    name = "graaf"
    description = (
        "Graaf: A Lightweight, Header-Only C++20 Graph Library."
    )
    license = "MIT"
    homepage = "https://github.com/bobluppes/graaf"
    topics = ("graph", "header-only")
    settings = "compiler"
    package_type = "header-library"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def validate(self):
        check_min_cppstd(self, 20)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE.md", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []

        self.cpp_info.set_property("cmake_file_name", "graaflib")
        self.cpp_info.set_property("cmake_target_name", "Graaf::Graaf")
