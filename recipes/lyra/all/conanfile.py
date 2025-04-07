import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.files import copy, get
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class LyraConan(ConanFile):
    name = "lyra"
    homepage = "https://bfgroup.github.io/Lyra/"
    description = "A simple to use, composing, header only, command line arguments parser for C++ 11 and beyond."
    topics = ("cli", "cli-parser", "argparse", "commandline",
              "flags", "header-only", "no-dependencies", "c++11")
    url = "https://github.com/conan-io/conan-center-index"
    license = "MIT"
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
        copy(self, "LICENSE.txt", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        copy(
            self, "*.h*",
            dst=os.path.join(self.package_folder, "include"),
            src=os.path.join(self.source_folder, "include"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "lyra")
        self.cpp_info.set_property("cmake_target_name", "bfg::lyra")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
