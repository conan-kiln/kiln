import os

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout


class TclapConan(ConanFile):
    name = "tclap"
    description = "Templatized Command Line Argument Parser"
    license = "MIT"
    homepage = "https://sourceforge.net/projects/tclap/"
    topics = ("parser", "command-line", "header-only")
    settings = "os", "arch", "compiler", "build_type"
    package_type = "header-library"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "COPYING", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*.h", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
