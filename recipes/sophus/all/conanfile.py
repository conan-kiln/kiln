import os

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class SophusConan(ConanFile):
    name = "sophus"
    description = "C++ implementation of Lie Groups using Eigen."
    license = "MIT"
    homepage = "https://strasdat.github.io/Sophus/"
    topics = ("eigen", "numerical", "math", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "with_fmt": [True, False],
    }
    default_options = {
        "with_fmt": True,
    }
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("eigen/3.4.0", transitive_headers=True)
        self.requires("fmt/[>=5]", transitive_headers=True)

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*.hpp", os.path.join(self.source_folder, "sophus"),
                            os.path.join(self.package_folder, "include", "sophus"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "Sophus")
        self.cpp_info.set_property("cmake_target_name", "Sophus::Sophus")
        self.cpp_info.set_property("pkg_config_name", "sophus")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        if not self.options.with_fmt:
            self.cpp_info.defines.append("SOPHUS_USE_BASIC_LOGGING=1")
