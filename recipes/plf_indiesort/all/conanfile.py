import os

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class PlfindiesortConan(ConanFile):
    name = "plf_indiesort"
    description = (
        "A sort wrapper enabling both use of random-access sorting on non-random "
        "access containers, and increased performance for the sorting of large types."
    )
    license = "Zlib"
    topics = ("algorithm", "sort", "header-only")
    homepage = "https://plflib.org/indiesort.htm"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def package_id(self):
        self.info.clear()

    def layout(self):
        basic_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version],
            destination=self.source_folder, strip_root=True)

    def build(self):
        pass

    def package(self):
        copy(self, "LICENSE.md", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        copy(self, "plf_indiesort.h", src=self.source_folder, dst=os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
