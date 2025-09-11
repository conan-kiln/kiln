import os
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class ConoptConan(ConanFile):
    name = "conopt"
    description = ("CONOPT is a general-purpose optimization system for large-scale nonlinear models. "
                   "CONOPT employs a feasible path algorithm that is based on active set methods, particularly suited to large, sparse models.")
    license = "Proprietary"
    homepage = "https://conopt.gams.com/"
    topics = ("optimization", "nonlinear-optimization", "gams")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "cxx": [True, False],
    }
    default_options = {
        "cxx": True,
    }

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))

    def package_id(self):
        if not self.info.options.cxx:
            if not is_apple_os(self.info):
                del self.info.settings.compiler
            del self.info.settings.build_type

    def layout(self):
        cmake_layout(self, src_folder="src")

    @cached_property
    def _download_info(self):
        if self.settings.os in ["Linux", "FreeBSD"]:
            os_ = "Linux"
        elif is_apple_os(self):
            os_ = "Macos"
        else:
            os_ = "Windows"
        arch = str(self.settings.arch)
        if "armv8" in arch:
            arch = "armv8"
        return self.conan_data["sources"][self.version].get(os_, {}).get(arch)

    def validate(self):
        if not self._download_info:
            raise ConanInvalidConfiguration(f"{self.settings.arch} {self.settings.os} is not supported")

    def _source(self):
        get(self, **self._download_info, strip_root=True, destination=self.source_folder)
        # Default COI_API to dllimport for consuming code
        replace_in_file(self, os.path.join(self.source_folder, "include/conopt.h"),
                        "__declspec(dllexport)",
                        "__declspec(dllimport)")
        if self.settings.os == "Windows":
            # Mark C++ symbols for export when building the C++ interface library
            replace_in_file(self, os.path.join(self.source_folder, "src/cpp/conopt.hpp"),
                            '#include "conopt.h"',
                            '#include "conopt.h"\n'
                            "#define COI_API __declspec(dllexport)")

    @property
    def _soversion(self):
        return self.version.split(".")[0]

    def generate(self):
        if self.options.cxx:
            tc = CMakeToolchain(self)
            tc.cache_variables["VERSION"] = self.version
            tc.cache_variables["SOVERSION"] = self._soversion
            tc.generate()

    def build(self):
        self._source()
        if self.options.cxx:
            cmake = CMake(self)
            cmake.configure()
            cmake.build()

    def package(self):
        copy(self, "*.h", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        lib_src = os.path.join(self.source_folder, "lib")
        lib_dst = os.path.join(self.package_folder, "lib")
        bin_dst = os.path.join(self.package_folder, "bin")
        if self.settings.os in ["Linux", "FreeBSD"]:
            copy(self, f"libconopt.so.{self.version}", lib_src, lib_dst)
            with chdir(self, lib_dst):
                os.symlink(f"libconopt.so.{self.version}", f"libconopt.so.{self._soversion}")
                os.symlink(f"libconopt.so.{self.version}", f"libconopt.so")
        elif is_apple_os(self):
            copy(self, f"libconopt.{self.version}.dylib", lib_src, lib_dst)
            with chdir(self, lib_dst):
                os.symlink(f"libconopt.{self.version}.dylib", f"libconopt.{self._soversion}.dylib")
                os.symlink(f"libconopt.{self.version}.dylib", f"libconopt.dylib")
            if self.settings.compiler != "gcc":
                copy(self, "libgcc_s.*", lib_src, lib_dst)
                copy(self, "libgfortran.*", lib_src, lib_dst)
                copy(self, "libgomp.*", lib_src, lib_dst)
                copy(self, "libquadmath.*", lib_src, lib_dst)
        else:
            copy(self, f"conopt{self._soversion}.lib", lib_src, lib_dst)
            copy(self, f"conopt{self._soversion}.dll", lib_src, bin_dst)
            copy(self, "libifcoremd.dll", lib_src, bin_dst)
            copy(self, "libiomp*.dll", lib_src, bin_dst)
            copy(self, "libmmd.dll", lib_src, bin_dst)
            copy(self, "svml_dispmd.dll", lib_src, bin_dst)
        if self.options.cxx:
            cmake = CMake(self)
            cmake.install()

    def package_info(self):
        # The CMake and pkg-config names are unofficial
        major_suffix = self._soversion if self.settings.os == "Windows" else ""
        self.cpp_info.components["conopt_"].set_property("cmake_target_name", "conopt")
        self.cpp_info.components["conopt_"].set_property("pkg_config_name", "conopt")
        self.cpp_info.components["conopt_"].libs = [f"conopt{major_suffix}"]

        if self.options.cxx:
            self.cpp_info.components["conoptcpp"].set_property("cmake_target_name", "conoptcpp")
            self.cpp_info.components["conoptcpp"].set_property("pkg_config_name", "conoptcpp")
            self.cpp_info.components["conoptcpp"].libs = [f"conoptcpp{major_suffix}"]
            self.cpp_info.components["conoptcpp"].requires = ["conopt_"]
