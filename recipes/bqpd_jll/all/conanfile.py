import os
import re
from functools import cached_property
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class BqpdJllConan(ConanFile):
    name = "bqpd_jll"
    description = "BQPD solves large, sparse or dense linear and quadratic programming problems"
    # "The underlying solver is a closed-source product.
    #  Although its source code is not publicly available, the precompiled binaries are freely redistributable under the BSD 3-Clause license.
    #  This package does not bundle any additional third-party code."
    license = "BSD 3-Clause"
    homepage = "https://github.com/leyffer/BQPD_jll.jl"
    topics = ("optimiztion", "linear-programming", "quadratic-programming", "pre-built")
    package_type = "static-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "gfortran_soversion": [3, 4, 5],
    }
    default_options = {
        "gfortran_soversion": 5,
    }
    languages = ["C"]

    def layout(self):
        basic_layout(self, src_folder="src")

    @cached_property
    def _platform_id(self):
        os_ = str(self.settings.os)
        arch = str(self.settings.arch)
        if is_apple_os(self):
            if "armv8" in arch:
                return "aarch64-apple-darwin"
            elif arch == "x86_64":
                return "x86_64-apple-darwin"
        elif os_ == "Linux":
            if arch == "armv8":
                return "aarch64-linux-gnu"
            elif arch == "armv6":
                return "armv6l-linux-gnueabihf"
            elif arch == "armv7":
                return "armv7l-linux-gnueabihf"
            elif arch == "x86":
                return "i686-linux-gnu"
            elif arch == "riscv64":
                return "riscv64-linux-gnu"
            elif arch == "x86_64":
                return "x86_64-linux-gnu"
            elif arch == "ppc64le":
                return "powerpc64le-linux-gnu"
        elif os_ == "FreeBSD":
            if arch == "x86_64":
                return "x86_64-unknown-freebsd"
            elif arch == "armv8":
                return "aarch64-unknown-freebsd"
        elif os_ == "Windows":
            if arch == "x86_64":
                return "x86_64-w64-mingw32"
            elif arch == "x86":
                return "i686-w64-mingw32"
        return None

    def validate(self):
        if self._platform_id is None:
            raise ConanInvalidConfiguration(f"{self.settings.os} {self.settings.arch} is not supported")

    @cached_property
    def _archives(self):
        download(self, **self.conan_data["sources"][self.version], filename="Artifact.toml")
        content = Path("Artifact.toml").read_text()
        urls = re.findall(r'url = "(.*?)"', content)
        sha256s = re.findall(r'sha256 = "(.*?)"', content)
        archives = {}
        for url, sha256 in zip(urls, sha256s):
            variant = url.rsplit(self.version + ".")[-1].replace(".tar.gz", "")
            archives[variant] = dict(url=url, sha256=sha256)
        return archives

    def package(self):
        variant = f"{self._platform_id}-libgfortran{self.options.gfortran_soversion}"
        get(self, **self._archives[variant], destination=self.package_folder)
        mkdir(self, os.path.join(self.package_folder, "licenses"))
        os.rename(os.path.join(self.package_folder, "share/licenses/BQPD/LICENSE"),
                  os.path.join(self.package_folder, "licenses/LICENSE"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        # The CMake and .pc names are not official
        self.cpp_info.set_property("cmake_file_name", "BQPD")

        self.cpp_info.components["bqpd"].set_property("cmake_target_name", "bqpd")
        self.cpp_info.components["bqpd"].set_property("pkg_config_name", "bqpd")
        self.cpp_info.components["bqpd"].libs = ["bqpd"]
        self.cpp_info.components["bqpd"].includedirs = []

        self.cpp_info.components["bqpd_dense"].set_property("cmake_target_name", "bqpd_dense")
        self.cpp_info.components["bqpd_dense"].set_property("pkg_config_name", "bqpd_dense")
        self.cpp_info.components["bqpd_dense"].libs = ["bqpd_dense"]
        self.cpp_info.components["bqpd_dense"].includedirs = []

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["bqpd"].system_libs = ["m"]
            self.cpp_info.components["bqpd_dense"].system_libs = ["m"]
            gfortran = "gfortran"
        elif is_apple_os(self):
            gfortran = f"gfortran.{self.options.gfortran_soversion}"
        else:
            gfortran = f"libgfortran-{self.options.gfortran_soversion}"
        self.cpp_info.components["bqpd"].system_libs.append(gfortran)
        self.cpp_info.components["bqpd_dense"].system_libs.append(gfortran)
