import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class FastPRNGConan(ConanFile):
    name = "fastprng"
    description = (
        "FAST 32/64 bit PRNG (pseudo-random generator), highly optimized, based "
        "on xoshiro* / xoroshiro*, xorshift and other Marsaglia algorithms."
    )
    topics = ("random", "prng", "xorshift", "xoshiro", )
    license = "BSD-2-Clause"
    homepage = "https://github.com/BrutPitt/fastPRNG"
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def validate(self):
        check_min_cppstd(self, "11")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "*.h", self.source_folder, os.path.join(self.package_folder, "include"))
        copy(self, "license.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
