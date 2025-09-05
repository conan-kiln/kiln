import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class TslOrderedMapConan(ConanFile):
    name = "tsl-ordered-map"
    license = "MIT"
    description = "C++ hash map and hash set which preserve the order of insertion."
    topics = ("ordered-map", "structure", "hash map", "hash set")
    homepage = "https://github.com/Tessil/ordered-map"
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

    def build(self):
        pass

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        copy(self, "*.h", src=os.path.join(self.source_folder, "include"), dst=os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "tsl-ordered-map")
        self.cpp_info.set_property("cmake_target_name", "tsl::ordered_map")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
