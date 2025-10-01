import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class RefxConan(ConanFile):
    name = "refx"
    description = "Compile-time safe C++ library for accurate coordinate transformations and navigation in mobile robotics."
    license = "MIT"
    homepage = "https://github.com/mosaico-labs/refx"
    topics = ("coordinate-transformation", "reference-frame", "robotics", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "with_eigen": [True, False],
    }
    default_options = {
        "with_eigen": True,
    }

    def package_id(self):
        self.info.clear()

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_eigen:
            self.requires("eigen/[>=3.4.0 <6]")

    def validate(self):
        check_min_cppstd(self, 17)

    def package(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        copy(self, "LICENSE", self.build_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.build_folder, "src", "include"), os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "refx")
        self.cpp_info.set_property("cmake_target_name", "refx::refx")
        if self.options.with_eigen:
            self.cpp_info.defines.append("REFX_ENABLE_EIGEN_SUPPORT")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
