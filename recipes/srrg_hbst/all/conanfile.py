import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class SrrgHbstConan(ConanFile):
    name = "srrg_hbst"
    description = "Hamming Binary Search Tree Header-only library"
    license = "BSD-3-Clause"
    homepage = "https://gitlab.com/saurabh1002/srrg_hbst"
    topics = ("binary-search-tree", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True
    options = {
        "with_eigen": [True, False],
        "with_opencv": [True, False],
    }
    default_options = {
        "with_eigen": True,
        "with_opencv": False,
    }

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_eigen:
            self.requires("eigen/[>=3.3 <6]")

    def package_id(self):
        self.info.clear()

    def validate(self):
        check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE*", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "srrg_hbst"), os.path.join(self.package_folder, "include", "srrg_hbst"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []

        if self.options.with_eigen:
            self.cpp_info.defines.append("SRRG_HBST_HAS_EIGEN")
            self.cpp_info.requires.append("eigen::eigen")
        if self.options.with_opencv:
            self.cpp_info.defines.append("SRRG_HBST_HAS_OPENCV")
            self.cpp_info.requires.append("opencv::opencv_core")
