import os
from functools import cached_property
from pathlib import Path

import yaml
from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class IntelDpcppSyclConan(ConanFile):
    name = "intel-dpcpp-sycl"
    description = "Intel oneAPI DPC++/C++ SYCL Compiler Runtime package"
    # https://intel.ly/393CijO
    license = "DocumentRef-license.txt:LicenseRef-Intel-DevTools-EULA"
    homepage = "https://www.intel.com/content/www/us/en/developer/tools/oneapi/data-parallel-c-plus-plus.html"
    topics = ("intel", "sycl", "pre-built")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"

    @cached_property
    def _packages(self):
        with open(os.path.join(self.recipe_folder, "sources", f"{self.version}.yml")) as f:
            return yaml.safe_load(f)[str(self.settings.os)]

    def export(self):
        copy(self, f"{self.version}.yml", os.path.join(self.recipe_folder, "sources"), os.path.join(self.export_folder, "sources"))

    def requirements(self):
        self.requires("umf/[<1]", options={"shared": True})
        self.requires(f"intel-ur/{self.version}")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type

    def layout(self):
        basic_layout(self, src_folder="src")

    def validate(self):
        if self.settings.os not in ["Linux", "FreeBSD", "Windows"]:
            raise ConanInvalidConfiguration(f"{self.settings.os} is not supported")
        if self.settings.arch != "x86_64":
            raise ConanInvalidConfiguration(f"{self.settings.arch} is not supported")
        if not self.dependencies["umf"].options.shared:
            raise ConanInvalidConfiguration("-o hwloc/*:shared=True is required")

    def _get_pypi_package(self, name):
        get(self, **self._packages[name], destination=self.build_folder, strip_root=True)

    def build(self):
        self._get_pypi_package("intel-sycl-rt")
        self._get_pypi_package("intel-cmplr-lib-rt")

    def package(self):
        if self.settings.os == "Windows":
            move_folder_contents(self, os.path.join(self.build_folder, "data", "Library"), self.package_folder)
            copy(self, "*", os.path.join(self.build_folder, "data"), self.package_folder)
        else:
            move_folder_contents(self, os.path.join(self.build_folder, "data"), self.package_folder)
        copy(self, "LICENSE.txt", self.build_folder, os.path.join(self.package_folder, "licenses"))
        # Don't vendor onnxruntime
        rm(self, "*onnxruntime*", os.path.join(self.package_folder, "lib"))
        rm(self, "*onnxruntime*", os.path.join(self.package_folder, "bin"))
        # Replace hard copies with symlinks
        if self.settings.os in ["Linux", "FreeBSD"]:
            libdir = Path(self.package_folder, "lib")
            for p in list(libdir.glob("*.so.*.*")) + list(libdir.glob("libintlc.so.*")):
                target = str(p.parent / p.name.split(".", 1)[0])
                for suffix in p.suffixes[:-1]:
                    target += suffix
                    target_path = Path(target)
                    if target_path.exists():
                        target_path.unlink()
                        target_path.symlink_to(p.name)

    def package_info(self):
        # Unofficial CMake and .pc targets
        self.cpp_info.set_property("cmake_file_name", "SYCL")
        self.cpp_info.set_property("cmake_target_name", "SYCL::SYCL")
        self.cpp_info.set_property("cmake_target_aliases", ["sycl"])
        self.cpp_info.set_property("pkg_config_name", "sycl")

        self.cpp_info.libs = ["sycl"]
        self.cpp_info.resdirs = ["opt", "lib/clang"]

        if self.settings.compiler == "msvc":
            self.cpp_info.cxxflags = ["/Zc:__cplusplus"]
