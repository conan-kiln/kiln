import os
from functools import cached_property

import yaml
from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class IntelOpenMPConan(ConanFile):
    name = "intel-openmp"
    description = "Intel OpenMP Runtime Library"
    # https://intel.ly/393CijO
    license = "DocumentRef-license.txt:LicenseRef-Intel-DevTools-EULA"
    homepage = "https://www.intel.com/content/www/us/en/docs/dpcpp-cpp-compiler/developer-guide-reference/2025-2/openmp-support.html"
    topics = ("intel", "openmp", "pre-built")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"

    @cached_property
    def _packages(self):
        with open(os.path.join(self.recipe_folder, "sources", f"{self.version}.yml")) as f:
            return yaml.safe_load(f)[str(self.settings.os)]

    def export(self):
        copy(self, f"{self.version}.yml", os.path.join(self.recipe_folder, "sources"), os.path.join(self.export_folder, "sources"))

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires(f"intel-ur/{self.version}")

    def validate(self):
        if self.settings.os not in ["Linux", "FreeBSD", "Windows"]:
            raise ConanInvalidConfiguration(f"{self.settings.os} is not supported")
        if self.settings.arch != "x86_64":
            raise ConanInvalidConfiguration(f"{self.settings.arch} is not supported")

    def _get_pypi_package(self, name):
        get(self, **self._packages[name], destination=self.build_folder, strip_root=True)

    def build(self):
        self._get_pypi_package("intel-openmp")

    def package(self):
        move_folder_contents(self, os.path.join(self.build_folder, "data"), self.package_folder)
        copy(self, "LICENSE.txt", self.build_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.package_folder, "share/doc/compiler/licensing/openmp"), os.path.join(self.package_folder, "licenses"))
        rm(self, "*.a", os.path.join(self.package_folder, "lib"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.libs = ["iomp5"]
        self.cpp_info.includedirs = ["opt/compiler/include"]
