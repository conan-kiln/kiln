import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class SevenZipConan(ConanFile):
    name = "7zip"
    description = "7-Zip is a file archiver with a high compression ratio"
    license = "LGPL-2.1-or-later AND BSD-3-Clause AND Unrar"
    homepage = "https://www.7-zip.org"
    topics = ("archive", "compression", "decompression", "zip", "pre-built")
    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    def validate(self):
        # TODO: add other platforms
        if self.settings.os != "Windows" or self.settings.arch != "x86_64":
            raise ConanInvalidConfiguration("Only x86_64 Windows is supported")

    def build_requirements(self):
        self.tool_requires("lessmsi/[*]")

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.build_type
        del self.info.settings.compiler

    def source(self):
        download(self, **self.conan_data["sources"][self.version], filename="7zip.msi")

    def build(self):
        self.run("lessmsi x 7zip.msi", cwd=self.source_folder)

    def package(self):
        copy(self, "License.txt", self.source_folder, os.path.join(self.package_folder, "licenses"), keep_path=False)
        copy(self, "*.exe", self.source_folder, os.path.join(self.package_folder, "bin"), keep_path=False)
        copy(self, "*.dll", self.source_folder, os.path.join(self.package_folder, "bin"), keep_path=False)

    def package_info(self):
        self.cpp_info.includedirs = []
        self.cpp_info.libdirs = []
