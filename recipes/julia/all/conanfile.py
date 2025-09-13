import os
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.files import *

required_conan_version = ">=2.1"


class JuliaConan(ConanFile):
    name = "julia"
    description = "The Julia Programming Language"
    license = "MIT"
    homepage = "https://julialang.org/"
    topics = ("julia", "pre-built")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"

    @cached_property
    def _platform(self):
        os_ = str(self.settings.os)
        arch = str(self.settings.arch)
        if is_apple_os(self):
            os_ = "Macos"
            if "armv8" in arch:
                arch = "armv8"
        return os_, arch

    @cached_property
    def _dl_info(self):
        os_, arch = self._platform
        return self.conan_data["sources"][self.version].get(os_, {}).get(arch)

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        self.info.settings.os, self.info.settings.arch = self._platform

    def validate(self):
        if self._dl_info is None:
            raise ConanInvalidConfiguration(f"{self.settings.arch} {self.settings.os} is not supported")

    def package(self):
        get(self, **self._dl_info, strip_root=True, destination=self.package_folder)
        mkdir(self, os.path.join(self.package_folder, "licenses"))
        os.rename(os.path.join(self.package_folder, "LICENSE.md"), os.path.join(self.package_folder, "licenses", "LICENSE.md"))
        rmdir(self, os.path.join(self.package_folder, "share", "doc"))
        rmdir(self, os.path.join(self.package_folder, "share", "man"))

    def package_info(self):
        self.cpp_info.libs = ["julia"]
        self.cpp_info.includedirs = ["include", "include/julia"]
        self.cpp_info.resdirs = ["share", "etc"]
