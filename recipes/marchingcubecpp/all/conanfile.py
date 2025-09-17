import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class MarchingCubeCppConan(ConanFile):
    name = "marchingcubecpp"
    description = "A public domain/MIT header-only marching cube implementation in C++ without anything fancy."
    license = "MIT OR public domain"
    homepage = "https://github.com/aparis69/MarchingCubeCpp"
    topics = ("marching-cube", "mesh", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def validate(self):
        check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # add a missing include
        replace_in_file(self, "MC.h",
                        "#include <cmath>",
                        "#include <cmath>\n#include <cstdint>")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "MC.h", self.source_folder, os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
