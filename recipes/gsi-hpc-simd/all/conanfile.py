import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class GsiHpcSimdConan(ConanFile):
    name = "gsi-hpc-simd"
    description = "Implementation of C++26 §29.10 Data-parallel types for GCC"
    license = "GPL-3.0-or-later WITH GCC-exception-3.1 OR LGPL-3.0-or-later"
    url = "https://github.com/GSI-HPC/simd"
    topics = ("c++26", "data-parallel-types", "simd", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def validate(self):
        check_min_cppstd(self, 20)
        compiler = self.settings.compiler
        if compiler == "gcc" and Version(compiler.version) < "14":
            raise ConanInvalidConfiguration(f"{self.ref} requires GCC >= 14")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        for license_file in [
            "GPL-3.0-or-later.txt",
            "GCC-exception-3.1.txt",
            "LGPL-3.0-or-later.txt",
        ]:
            copy(self, license_file, os.path.join(self.source_folder, "LICENSES"), os.path.join(self.package_folder, "licenses"))
        copy(self, "simd", self.source_folder, os.path.join(self.package_folder, "include"))
        copy(self, "*", os.path.join(self.source_folder, "bits"), os.path.join(self.package_folder, "include", "bits"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
