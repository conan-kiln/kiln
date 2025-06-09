import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class PopplerDataConan(ConanFile):
    name = "poppler-data"
    description = "encoding files for use with poppler, enable CJK and Cyrrilic"
    license = "(GPL-2.0-only OR GPL-3.0-only) AND BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://poppler.freedesktop.org/"
    topics = "poppler", "pdf", "rendering", "header-only"

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING*", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join("share", "pkgconfig"))

    @property
    def _poppler_datadir(self):
        return os.path.join(self.package_folder, "share", "poppler")

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "poppler-data")
        self.cpp_info.bindirs = []
        self.cpp_info.includedirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = ["share"]
        self.cpp_info.defines = ["POPPLER_DATADIR={}".format(self._poppler_datadir.replace("\\", "//"))]
        self.conf_info.define("user.poppler-data:datadir", self._poppler_datadir)
