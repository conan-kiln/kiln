import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc

required_conan_version = ">=2.1"

class CSVMONEKYConan(ConanFile):
    name = "csvmonkey"
    description = "Header-only vectorized, lazy-decoding, zero-copy CSV file parser"
    license = "BSD-3-Clause"
    homepage = "https://github.com/dw/csvmonkey/"
    topics = ("csv-parser", "header-only", "vectorized", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "with_spirit": [True, False],
    }
    default_options = {
        "with_spirit": False,
    }
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_spirit:
            self.requires("boost/[^1.71.0]", libs=False)

    def package_id(self):
        self.info.clear()

    def validate(self):
        check_min_cppstd(self, 11)

        if self.settings.arch not in ("x86", "x86_64",):
            raise ConanInvalidConfiguration(f"{self.ref} requires x86 architecture.")

        if is_msvc(self):
            raise ConanInvalidConfiguration(f"{self.ref} doesn't support Visual Studio C++.")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        copy(self, "*.hpp", dst=os.path.join(self.package_folder, "include"), src=os.path.join(self.source_folder, "include"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []

        self.cpp_info.set_property("cmake_file_name", "csvmonkey")
        self.cpp_info.set_property("cmake_target_name", "csvmonkey::csvmonkey")
        self.cpp_info.set_property("pkg_config_name", "csvmonkey")

        if self.options.with_spirit:
            self.cpp_info.defines.append("USE_SPIRIT")
