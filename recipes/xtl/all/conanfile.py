import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class XtlConan(ConanFile):
    name = "xtl"
    license = "BSD-3-Clause"
    homepage = "https://github.com/xtensor-stack/xtl"
    description = "The x template library"
    topics = ("templates", "containers", "algorithms")
    settings = "os", "arch", "compiler", "build_type"
    package_type = "header-library"
    no_copy_source = True

    def package_id(self):
        self.info.clear()

    def validate(self):
        check_min_cppstd(self, 14 if Version(self.version) < "0.8" else 17)

    def layout(self):
        basic_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        copy(self, "*.hpp", src=os.path.join(self.source_folder, "include"), dst=os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "xtl")
        self.cpp_info.set_property("cmake_target_name", "xtl")
        self.cpp_info.set_property("pkg_config_name", "xtl")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
