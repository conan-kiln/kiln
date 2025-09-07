import os
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc_static_runtime

required_conan_version = ">=2.4"


class XpressConan(ConanFile):
    name = "xpress"
    description = ("The FICO Xpress optimizer is a commercial optimization solver for linear programming (LP),"
                   " mixed integer linear programming (MILP), convex quadratic programming (QP),"
                   " convex quadratically constrained quadratic programming (QCQP),"
                   " second-order cone programming (SOCP) and their mixed integer counterparts.")
    license = "DocumentRef-license.txt:LicenseRef-FICO-Xpress-Shrinkwrap-License-Agreement"
    homepage = "https://www.fico.com/en/products/fico-xpress-optimization"
    topics = ("optimization", "linear-programming", "mixed-integer-programming", "quadratic-programming", "solver", "mosel")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "cxx": [True, False],
        "tools": [True, False],
    }
    default_options = {
        "shared": False,
        "cxx": True,
        "tools": False,
    }

    def configure(self):
        if self.options.cxx:
            # xprscxx requires a shared xprs library
            self.options.shared.value = True
        else:
            self.languages = ["C"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type

    def validate(self):
        if self.settings.os in ["Linux", "FreeBSD"]:
            if self.settings.arch != "x86_64":
                raise ConanInvalidConfiguration("Only x86_64 is supported on Linux and FreeBSD")
        elif self.settings.os == "Windows":
            if self.settings.arch != "x86_64":
                raise ConanInvalidConfiguration("Only x86_64 is supported on Windows")
            if self.settings.compiler != "msvc":
                raise ConanInvalidConfiguration("Only MSVC is supported on Windows")
        elif is_apple_os(self):
            # TODO
            raise ConanInvalidConfiguration(f"{self.settings.os} is not yet supported")
        else:
            raise ConanInvalidConfiguration("Only Linux, Windows and macOS are supported")
        if self.options.cxx:
            check_min_cppstd(self, 17)

    @property
    def _download_info(self):
        if self.settings.os in ["Linux", "FreeBSD"]:
            return self.conan_data["sources"][self.version]["Linux"]
        elif self.settings.os == "Windows":
            return self.conan_data["sources"][self.version]["Windows"]
        else:
            arch = "x86_64" if self.settings.arch == "x86_64" else "armv8"
            return self.conan_data["sources"][self.version]["macOS"][arch]

    @property
    def _archive_dir(self):
        return self.conf.get("user.tools:offline_archives_folder", check_type=str, default=None)

    @property
    def _file_name(self):
        return self._download_info["url"].rsplit("/", 1)[-1]

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
        if self.settings.os in ["Linux", "FreeBSD"]:
            unzip(self, self._archive_path, strip_root=True)
            tgz_path = str(next(Path(self.build_folder).rglob("*.tar.gz")))
            unzip(self, tgz_path, destination=self.source_folder)
        elif self.settings.os == "Windows":
            # FIXME: silent install does not work, it still prompts for UAC elevation
            #  Patching the .exe manifest would help, but this fails due to AV
            self.output.warning("A UAC prompt will open for the installer, please accept it.")
            self.run(f'"{self._archive_path}" /a /s /v"/quiet TARGETDIR={self.source_folder}"')
            rm(self, "*.msi", self.source_folder, recursive=True)
            move_folder_contents(self, os.path.join(self.source_folder, "xpressmp"), self.source_folder)
        else:
            # TODO
            raise NotImplementedError

    def build(self):
        self._source()

    @property
    def _bindrv_suffix(self):
        if self.settings.os == "Windows":
            return "MT" if is_msvc_static_runtime(self) else "MD"
        return ""

    def package(self):
        copy(self, "*", os.path.join(self.source_folder, "licenses"), os.path.join(self.package_folder, "licenses"))
        copy(self, "*.h", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        if self.options.cxx:
            copy(self, "*.hpp", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
            copy(self, "*.cpp", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))

        def _copy_library(name, static=False):
            if self.settings.os in ["Linux", "FreeBSD"]:
                if static:
                    copy(self, f"lib{name}.a", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
                else:
                    copy(self, f"lib{name}.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
            elif is_apple_os(self):
                if static:
                    copy(self, f"lib{name}.a", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
                else:
                    copy(self, f"lib{name}.dylib", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
            else:
                if static:
                    copy(self, f"{name}.lib", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
                else:
                    copy(self, f"{name}.lib", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
                    copy(self, f"{name}.dll", os.path.join(self.source_folder, "bin"), os.path.join(self.package_folder, "bin"))

        if not self.options.shared:
            _copy_library("xprs-static", static=True)
        _copy_library("xprs")
        if self.options.cxx:
            _copy_library("xprscxx")
        _copy_library("xprl")
        _copy_library("xprnls")
        _copy_library("xprm_mc")
        _copy_library("xprm_rt")
        _copy_library("bindrv" + self._bindrv_suffix, static=True)
        _copy_library("xprd", static=True)
        _copy_library("Kalis")
        copy(self, "*xprl*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))

        copy(self, "*", os.path.join(self.source_folder, "do"), os.path.join(self.package_folder, "do"))
        copy(self, "*", os.path.join(self.source_folder, "dso"), os.path.join(self.package_folder, "dso"))

        system_dlls = ["api-ms-*.dll", "mfc*.dll", "vs*.dll", "*J.dll", "*crt*.dll"]
        if self.settings.os == "Windows":
            copy(self, "*.dll", os.path.join(self.source_folder, "bin"), os.path.join(self.package_folder, "bin"), excludes=system_dlls)
        else:
            copy(self, "*", os.path.join(self.source_folder, "lib", "thirdparty"), os.path.join(self.package_folder, "lib", "thirdparty"))
        if self.options.tools:
            copy(self, "*", os.path.join(self.source_folder, "bin"), os.path.join(self.package_folder, "bin"), excludes=system_dlls)


    def package_info(self):
        # Optimizer library
        self.cpp_info.components["xprs"].libs = ["xprs" if self.options.shared else "xprs-static"]
        self.cpp_info.components["xprs"].requires = ["xprl"]
        if not self.options.shared and self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["xprs"].system_libs = ["m", "pthread", "dl"]

        # Optimizer library - C++ interface
        if self.options.cxx:
            self.cpp_info.components["xprscxx"].libs = ["xprscxx"]
            self.cpp_info.components["xprscxx"].requires = ["xprs"]
            if self.settings.compiler == "msvc":
                self.cpp_info.components["xprscxx"].cxxflags.append("/Zc:__cplusplus")

        # Xpress support library
        self.cpp_info.components["xprl"].libs = ["xprl"]

        # National language support
        self.cpp_info.components["xprnls"].libs = ["xprnls"]

        # Mosel compiler library
        self.cpp_info.components["xprm_mc"].libs = ["xprm_mc"]
        self.cpp_info.components["xprm_mc"].requires = ["xprm_rt", "xprnls"]

        # Mosel runtime library
        self.cpp_info.components["xprm_rt"].libs = ["xprm_rt"]
        self.cpp_info.components["xprm_rt"].requires = ["xprnls"]

        # Mosel binary format reader/writer
        self.cpp_info.components["bindrv"].libs = ["bindrv" + self._bindrv_suffix]

        # Mosel remote invocation library
        self.cpp_info.components["xprd"].libs = ["xprd"]

        # kalis.dso runtime dep
        self.cpp_info.components["Kalis"].libs = ["Kalis"]
        self.cpp_info.components["Kalis"].requires = ["xprl", "xprs"]
