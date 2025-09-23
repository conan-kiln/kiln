import os

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class LBFGSppConan(ConanFile):
    name = "lbfgspp"
    description = ("LBFGS++ is a header-only C++ library that implements the Limited-memory BFGS algorithm (L-BFGS)"
                   " for unconstrained minimization problems, and a modified version of the L-BFGS-B algorithm for box-constrained ones.")
    license = "MIT"
    homepage = "https://github.com/yixuan/LBFGSpp"
    topics = ("optimization", "lbfgsb", "limited-memory", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("eigen/3.4.0")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE*", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "lbfgspp")
        self.cpp_info.set_property("cmake_target_name", "lbfgspp")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
