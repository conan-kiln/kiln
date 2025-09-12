import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class SassyConan(ConanFile):
    name = "sassy"
    description = "The sassy preprocessor for symmetry detection"
    license = "MIT"
    homepage = "https://github.com/markusa4/sassy"
    topics = ("graph-theory", "symmetry")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def validate(self):
        check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE*", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*.h", self.source_folder, os.path.join(self.package_folder, "include", "sassy"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
