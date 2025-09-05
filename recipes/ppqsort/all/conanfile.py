import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.files import get, copy
from conan.tools.layout import basic_layout

required_conan_version = ">=2.9.0"


class PPQSortConan(ConanFile):
    name = "ppqsort"
    description = "Parallel Pattern Quicksort"
    license = "MIT"
    homepage = "https://github.com/GabTux/PPQSort"
    topics = ("algorithms", "sorting", "parallel", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    implements = ["auto_header_only"]
    no_copy_source = True

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def layout(self):
        basic_layout(self, src_folder="src")

    def validate(self):
        check_min_cppstd(self, 20)

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "include/*", self.source_folder, self.package_folder)

    def package_info(self):
        self.cpp_info.set_property("cmake_target_name", "PPQSort::PPQSort")
        self.cpp_info.set_property("cmake_file_name", "PPQSort")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["pthread"]
