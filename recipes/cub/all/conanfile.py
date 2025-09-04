import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class CubConan(ConanFile):
    name = "cub"
    description = "Cooperative primitives for CUDA C++"
    license = "BSD 3-Clause"
    homepage = "https://github.com/NVIDIA/cccl/tree/main/cub"
    topics = ("algorithms", "cuda", "gpu", "nvidia", "nvidia-hpc-sdk", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def requirements(self):
        if Version(self.version) >= "2.0":
            self.requires(f"libcudacxx/{self.version}")

    def validate(self):
        check_min_cppstd(self, 14)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        if Version(self.version) >= "2.2":
            move_folder_contents(self, os.path.join(self.source_folder, "cub"), self.source_folder)

    def package(self):
        copy(self, "LICENSE.TXT", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "cub"), os.path.join(self.package_folder, "include", "cub"))

    def package_info(self):
        # Follows the naming conventions of the official CMake config file:
        # https://github.com/NVIDIA/cccl/blob/main/lib/cmake/cub/cub-config.cmake
        self.cpp_info.set_property("cmake_file_name", "cub")
        self.cpp_info.set_property("cmake_target_name", "CUB::CUB")

        self.cpp_info.bindirs = []
        self.cpp_info.frameworkdirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = []
