import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class DirectXMathConan(ConanFile):
    name = "directxmath"
    description = "DirectXMath is an all inline SIMD C++ linear algebra library for use in games and graphics apps"
    license = "MIT"
    homepage = "https://github.com/microsoft/DirectXMath"
    topics = ("math", "simd", "directx", "graphics", "gamedev")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def package_id(self):
        self.info.clear()

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.get_safe("build_directxsh"):
            self.requires("directx-headers/[^1]")

    def validate(self):
        check_min_cppstd(self, 11)
        if self.options.get_safe("build_directxsh"):
            check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version]["sources"], strip_root=True)
        download(self, **self.conan_data["sources"][self.version]["sal.h"], filename="Inc/sal.h")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "Inc"), os.path.join(self.package_folder, "include"))
        copy(self, "*.h", os.path.join(self.source_folder, "XDSP"), os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "directxmath")
        self.cpp_info.set_property("cmake_target_name", "Microsoft::DirectXMath")
        self.cpp_info.set_property("cmake_target_aliases", ["Microsoft::XDSP"])
        self.cpp_info.set_property("cmake_config_version_compat", "AnyNewerVersion")
        self.cpp_info.set_property("pkg_config_name", "DirectXMath")

        # Skipping the building and installation of the optional DirectXSH static library
