import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class BazelConan(ConanFile):
    name = "bazel"
    description = "Bazel is a fast, scalable, multi-language and extensible build system."
    license = "Apache-2.0"
    homepage = "https://bazel.build/"
    topics = ("test", "build", "automation", "pre-built")
    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type

    @property
    def _binary_info(self):
        os = str(self.settings.os)
        arch = str(self.settings.arch)
        return self.conan_data["sources"][self.version][os].get(arch)

    def validate(self):
        if self.settings.os not in ["Linux", "Macos", "Windows"]:
            raise ConanInvalidConfiguration("Only Linux, Windows and OSX are supported for this package.")
        if self._binary_info is None:
            raise ConanInvalidConfiguration(
                f"{self.settings.arch} architecture on {self.settings.os} is not supported for this package."
            )

    @property
    def _program_suffix(self):
        return ".exe" if self.settings.os == "Windows" else ""

    @staticmethod
    def _chmod_plus_x(name):
        os.chmod(name, os.stat(name).st_mode | 0o111)

    def package(self):
        download(self, **self.conan_data["sources"][self.version]["license"],
                 filename=os.path.join(self.package_folder, "licenses", "LICENSE"))
        bazel_exe = os.path.join(self.package_folder, "bin", "bazel" + self._program_suffix)
        download(self, **self._binary_info, filename=bazel_exe)
        self._chmod_plus_x(bazel_exe)

    def package_info(self):
        self.cpp_info.libdirs = []
        self.cpp_info.includedirs = []
