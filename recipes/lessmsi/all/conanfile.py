import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *

required_conan_version = ">=2.1"


class LessmsiConan(ConanFile):
    name = "lessmsi"
    description = "A tool to view and extract the contents of an Windows Installer (.msi) file."
    license = "MIT"
    homepage = "https://github.com/activescott/lessmsi"
    topics = ("msi", "extraction", "pre-built")
    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type

    def validate(self):
        if self.settings.os != "Windows" or self.settings.arch != "x86_64":
            raise ConanInvalidConfiguration("Only Windows x86_64 is supported")

    def package(self):
        get(self, **self.conan_data["sources"][self.version], destination=os.path.join(self.package_folder, "bin"))
        download(self, **self.conan_data["license"][0], filename=os.path.join(self.package_folder, "licenses", "LICENSE"))

    def package_info(self):
        self.cpp_info.libdirs = []
        self.cpp_info.includedirs = []
