import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class GchSmallVectorConan(ConanFile):
    name = "gch-small-vector"
    description = "gch::small_vector is a vector container implementation with a small buffer optimization."
    license = "MIT"
    homepage = "https://github.com/gharveymn/small_vector"
    topics = ("container", "small-buffer-optimization", "header-only")
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

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*.hpp", os.path.join(self.source_folder, "source", "include"), os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "small_vector")
        self.cpp_info.set_property("cmake_target_name", "gch::small_vector")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
