import os
import platform

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class MetallConan(ConanFile):
    name = "metall"
    description = "Meta allocator for persistent memory"
    license = "MIT", "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/LLNL/metall"
    topics = "cpp", "allocator", "memory-allocator", "persistent-memory", "ecp", "exascale-computing"
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("boost/[^1.71.0 <1.85]")

    def package_id(self):
        self.info.clear()

    @property
    def _is_glibc_older_than_2_27(self):
        libver = platform.libc_ver()
        return self.settings.os == "Linux" and libver[0] == "glibc" and Version(libver[1]) < "2.27"

    def validate(self):
        check_min_cppstd(self, 17)

    def validate_build(self):
        if Version(self.version) >= "0.28" and self._is_glibc_older_than_2_27:
            raise ConanInvalidConfiguration(
                f"{self.ref} requires copy_file_range() which is available since glibc 2.27.")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build(self):
        pass

    def package(self):
        copy(self, "*", src=os.path.join(self.source_folder, "include"), dst=os.path.join(self.package_folder, "include"))
        copy(self, "LICENSE*", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        copy(self, "COPYRIGHT", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "Metall")
        self.cpp_info.set_property("cmake_target_name", "Metall::Metall")

        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("pthread")

        if self.settings.compiler == "gcc" or (self.settings.os == "Linux" and self.settings.compiler == "clang"):
            if Version(self.settings.compiler.version) < "9":
                self.cpp_info.system_libs += ["stdc++fs"]

        self.cpp_info.requires = ["boost::headers"]
