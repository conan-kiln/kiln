import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class QSoptConan(ConanFile):
    name = "qsopt"
    description = "QSopt provides functions for creating, manipulating, and solving LP problems"
    license = "DocumentRef-LICENSE:LicenseRef-QSOpt-non-commercial"
    homepage = "https://www.math.uwaterloo.ca/~bico/qsopt/"
    topics = ("linear-programming", "solver", "optimization")
    package_type = "static-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "tools": [True, False],
    }
    default_options = {
        "tools": False,
    }
    languages = ["C"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        if self.settings.os not in ["Linux", "FreeBSD"] or self.settings.arch != "x86_64":
            raise ConanInvalidConfiguration(f"{self.settings.arch} {self.settings.os} is not yet supported.")

    @staticmethod
    def _chmod_plus_x(name):
        if os.name == "posix":
            os.chmod(name, os.stat(name).st_mode | 0o111)

    def package(self):
        # Copied from https://www.math.uwaterloo.ca/~bico/qsopt/
        save(self, os.path.join(self.package_folder, "licenses", "LICENSE"),
             "QSopt can be used at no cost for research or education purposes; "
             "all rights to QSopt are maintained by the authors, David Applegate, William Cook, Sanjeeb Dash, and Monika Mevenkamp.")
        info = self.conan_data["sources"][self.version]["Linux"]
        download(self, **info["lib"], filename=os.path.join(self.package_folder, "lib", "libqsopt.a"))
        download(self, **info["header"], filename=os.path.join(self.package_folder, "include", "qsopt.h"))
        if self.options.tools:
            download(self, **info["executable"], filename=os.path.join(self.package_folder, "bin", "qsopt"))
            self._chmod_plus_x(os.path.join(self.package_folder, "bin", "qsopt"))

    def package_info(self):
        self.cpp_info.set_property("cmake_target_aliases", ["qsopt"])
        self.cpp_info.libs = ["qsopt"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]
