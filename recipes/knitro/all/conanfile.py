import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import cmake_layout, CMakeToolchain, CMakeDeps, CMake
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.4"


class KnitroConan(ConanFile):
    name = "knitro"
    description = "Artelys Knitro is a commercial software package for solving large scale nonlinear mathematical optimization problems."
    license = "DocumentRef-LICENSE:LicenseRef-Knitro-EULA"
    homepage = "https://www.artelys.com/solvers/knitro/"
    topics = ("optimization", "nonlinear-programming", "quadratic-programming", "mixed-integer-programming")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "cxx": [True, False],
    }
    default_options = {
        "shared": False,
        "cxx": True,
    }

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, self.export_sources_folder)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.shared
            self.package_type = "shared-library"

    def configure(self):
        if not self.options.cxx:
            self.languages = ["C"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.cxx:
            self.requires("openmp/system")

    @property
    def _download_info(self):
        if self.settings.os in ["Linux", "FreeBSD"]:
            os_ = "Linux"
        elif is_apple_os(self):
            os_ = "Macos"
        elif self.settings.os == "Windows":
            os_ = "Windows"
        arch = str(self.settings.arch)
        if "armv8" in arch:
            arch = "armv8"
        return self.conan_data["sources"][self.version].get(os_, {}).get(arch)

    def validate(self):
        if not self._download_info:
            raise ConanInvalidConfiguration(
                f"{self.settings.arch} {self.settings.os} is not supported for {self.ref}"
            )
        if self.options.cxx:
            check_min_cppstd(self, 11)

    @property
    def _archive_dir(self):
        return self.conf.get("user.tools:offline_archives_folder", check_type=str, default=None)

    @property
    def _file_name(self):
        return self._download_info["filename"]

    @property
    def _archive_path(self):
        return os.path.join(self._archive_dir, self._file_name)

    def validate_build(self):
        if not self._archive_dir:
            raise ConanInvalidConfiguration(f"user.tools:offline_archives_folder config variable must be set"
                                            f" to a location containing a {self._file_name} archive file.")
        if not os.path.isfile(self._archive_path):
            raise ConanInvalidConfiguration(
                f"{self._file_name} not found in {self._archive_dir}. "
                f"Please download it from {self._download_info['url']} and place it there."
            )

    def _source(self):
        check_sha256(self, self._archive_path, self._download_info["sha256"])
        unzip(self, self._archive_path, destination=self.source_folder, strip_root=True)
        copy(self, "CMakeLists.txt", self.export_sources_folder, os.path.join(self.source_folder, "examples", "C++"))
        # Use dllimport by default in consuming code
        replace_in_file(self, os.path.join(self.source_folder, "include/knitro.h"),
                        "KNITRO_API __stdcall",
                        "KNITRO_API __declspec(dllimport) __stdcall")

    def generate(self):
        if self.options.cxx:
            tc = CMakeToolchain(self)
            tc.cache_variables["KN_RELEASE"] = self._dll_suffix
            tc.cache_variables["VERSION"] = self.version
            tc.cache_variables["SOVERSION"] = self.version.split(".")[0]
            tc.generate()
            deps = CMakeDeps(self)
            deps.generate()

    def build(self):
        self._source()
        if self.options.cxx:
            cmake = CMake(self)
            cmake.configure(build_script_folder="examples/C++")
            cmake.build()

    @property
    def _dll_suffix(self):
        v = Version(self.version)
        return f"{v.major}{v.minor}{v.patch}"

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "licenses"), os.path.join(self.package_folder, "licenses", "third_party"))
        copy(self, "*.h", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        libdir = os.path.join(self.source_folder, "lib")
        if self.settings.os in ["Linux", "FreeBSD"]:
            if self.options.shared:
                copy(self, "*.so*", libdir, os.path.join(self.package_folder, "lib"))
            else:
                copy(self, "*.a", libdir, os.path.join(self.package_folder, "lib"))
            copy(self, "libiomp5.so", libdir, os.path.join(self.package_folder, "lib"))
        elif is_apple_os(self):
            if self.options.shared:
                copy(self, "*.dylib*", libdir, os.path.join(self.package_folder, "lib"))
            else:
                copy(self, "*.a", libdir, os.path.join(self.package_folder, "lib"))
            copy(self, "libiomp5.dylib", libdir, os.path.join(self.package_folder, "lib"))
            copy(self, "libirc.dylib", libdir, os.path.join(self.package_folder, "lib"))
        else:
            copy(self, f"knitro{self._dll_suffix}.lib", libdir, os.path.join(self.package_folder, "lib"))
            copy(self, f"knitro{self._dll_suffix}.dll", libdir, os.path.join(self.package_folder, "bin"))
            copy(self, "libiomp5md.dll", libdir, os.path.join(self.package_folder, "bin"))
        if self.options.cxx:
            cmake = CMake(self)
            cmake.install()

    def package_info(self):
        suffix = self._dll_suffix if self.settings.os == "Windows" else ""
        self.cpp_info.components["core"].set_property("cmake_target_name", "knitro")
        self.cpp_info.components["core"].set_property("cmake_target_aliases", [f"knitro{self._dll_suffix}"])
        self.cpp_info.components["core"].libs = ["knitro" + suffix]
        if self.settings.os in ["Linux", "FreeBSD"] and not self.options.shared:
            self.cpp_info.components["core"].system_libs = ["pthread", "m", "dl", "rt", "iomp5", "stdc++", "gcc_s"]
        elif is_apple_os(self) and not self.options.shared:
            self.cpp_info.components["core"].system_libs = ["c++", "iomp5"]

        if self.options.cxx:
            self.cpp_info.components["cxx"].set_property("cmake_target_name", "knitrocpp")
            self.cpp_info.components["cxx"].libs = ["knitrocpp"]
            if self.settings.compiler == "msvc":
                self.cpp_info.components["cxx"].cxxflags = ["/Zc:__cplusplus"]
            self.cpp_info.components["cxx"].requires = ["core", "openmp::openmp"]
