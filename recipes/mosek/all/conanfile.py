import os
from functools import cached_property
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class MosekConan(ConanFile):
    name = "mosek"
    description = ("MOSEK is a software package for the solution of linear, mixed-integer linear,"
                   " quadratic, mixed-integer quadratic, quadratically constrained,"
                   " conic and convex nonlinear mathematical optimization problems.")
    license = "DocumentRef-mosek-eula.pdf:LicenseRef-MOSEK-EULA"
    homepage = "https://www.mosek.com/"
    topics = ("optimization", "linear-programming", "mixed-integer-programming", "quadratic-programming")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fusion_cxx": [True, False],
        "tools": [True, False],
    }
    default_options = {
        "shared": True,
        "fusion_cxx": True,
        "tools": False,
    }

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, self.export_sources_folder)

    def configure(self):
        if not self.options.fusion_cxx:
            del self.options.shared

    def package_id(self):
        if not self.info.options.fusion_cxx:
            del self.info.settings.compiler
            del self.info.settings.build_type

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        # libtbb.so.12 is required
        self.requires("onetbb/[>=2021]", headers=False)

    def validate(self):
        if self.settings.os in ["Linux", "FreeBSD"]:
            if self.settings.arch not in ["x86_64", "armv8"]:
                raise ConanInvalidConfiguration("Only x86_64 and armv8 are supported on Linux")
        elif self.settings.os == "Windows":
            if self.settings.arch != "x86_64":
                raise ConanInvalidConfiguration("Only x86_64 is supported on Windows")
        elif is_apple_os(self):
            if not "armv8" in str(self.settings.arch):
                raise ConanInvalidConfiguration("Only armv8 is supported on macOS")
        else:
            raise ConanInvalidConfiguration("Only Linux, Windows and Macos are supported")
        if self.options.fusion_cxx:
            check_min_cppstd(self, 11)

    def _source(self):
        if self.settings.os in ["Linux", "FreeBSD"]:
            os_ = "Linux"
        elif is_apple_os(self):
            os_ = "Macos"
        else:
            os_ = "Windows"
        arch = str(self.settings.arch) if not is_apple_os(self) else "armv8"
        get(self, **self.conan_data["sources"][self.version][os_][arch], strip_root=True)
        package_root = next(Path(self.build_folder).rglob("fusion_cxx")).parent.parent
        copy(self, "*/mosek-eula.pdf", self.build_folder, package_root, keep_path=False)
        move_folder_contents(self, package_root, self.source_folder)
        if self.options.fusion_cxx:
            copy(self, "CMakeLists.txt", self.export_sources_folder, os.path.join(self.source_folder, "src", "fusion_cxx"))

    @cached_property
    def _dll_suffix(self):
        if self.settings.os == "Windows":
            v = Version(self.version)
            return f"_{v.major}_{v.minor}"
        return ""

    def generate(self):
        if self.options.fusion_cxx:
            v = Version(self.version)
            tc = CMakeToolchain(self)
            tc.cache_variables["BUILD_SHARED_LIBS"] = self.options.shared
            tc.cache_variables["MOSEK_VERSION"] = f"{v.major}.{v.minor}"
            tc.cache_variables["DLL_SUFFIX"] = self._dll_suffix
            tc.generate()

    def build(self):
        self._source()
        if self.options.fusion_cxx:
            cmake = CMake(self)
            cmake.configure(build_script_folder="src/fusion_cxx")
            cmake.build()

    def package(self):
        copy(self, "mosek-eula.pdf", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "h"), os.path.join(self.package_folder, "include"))
        if self.settings.os == "Windows":
            if self.settings.compiler == "msvc":
                copy(self, f"mosek64{self._dll_suffix}.lib", os.path.join(self.source_folder, "bin"), os.path.join(self.package_folder, "lib"))
            else:
                copy(self, f"libmosek64{self._dll_suffix}.a", os.path.join(self.source_folder, "bin"), os.path.join(self.package_folder, "lib"))
            copy(self, f"mosek64{self._dll_suffix}.dll", os.path.join(self.source_folder, "bin"), os.path.join(self.package_folder, "bin"))
        else:
            copy(self, "libmosek64.*", os.path.join(self.source_folder, "bin"), os.path.join(self.package_folder, "lib"))
        if self.options.tools:
            rm(self, "*fusion64*", os.path.join(self.source_folder, "bin"))
            rm(self, "*mosek64*", os.path.join(self.source_folder, "bin"))
            rm(self, "*mosekjava*", os.path.join(self.source_folder, "bin"))
            rm(self, "*mosekdotnet*", os.path.join(self.source_folder, "bin"))
            rm(self, "*tbb*", os.path.join(self.source_folder, "bin"))
            rm(self, "*.jar", os.path.join(self.source_folder, "bin"))
            copy(self, "*", os.path.join(self.source_folder, "bin"), os.path.join(self.package_folder, "bin"))
        if self.options.fusion_cxx:
            cmake = CMake(self)
            cmake.install()

    def package_info(self):
        self.cpp_info.components["mosek64"].set_property("cmake_target_name", "mosek64")
        self.cpp_info.components["mosek64"].libs = [f"mosek64{self._dll_suffix}"]

        if self.options.fusion_cxx:
            self.cpp_info.components["fusion64"].set_property("cmake_target_name", "fusion64")
            self.cpp_info.components["fusion64"].libs = [f"fusion64{self._dll_suffix}"]
            self.cpp_info.components["fusion64"].requires = ["mosek64"]
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.components["fusion64"].system_libs = ["m"]
