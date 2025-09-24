import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class ModernGpuConan(ConanFile):
    name = "moderngpu"
    description = "Patterns and behaviors for GPU computing"
    license = "BSD-2-Clause"
    homepage = "https://github.com/moderngpu/moderngpu"
    topics = ("gpu", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    no_copy_source = True

    python_requires = "conan-cuda/latest"
    python_requires_extend = "conan-cuda.Cuda"

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def requirements(self):
        self.cuda.requires("cudart")

    def validate(self):
        check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE.md", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "src"), os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
