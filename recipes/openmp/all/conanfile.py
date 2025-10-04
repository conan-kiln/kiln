from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class PackageConan(ConanFile):
    name = "openmp"
    description = "Conan meta-package for OpenMP (Open Multi-Processing)"
    license = "MIT"
    homepage = "https://www.openmp.org/"
    topics = ("parallelism", "multiprocessing")
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "provider": ["auto", "native", "llvm"],
    }
    default_options = {
        "provider": "auto",
    }

    def layout(self):
        basic_layout(self, src_folder="src")

    def config_options(self):
        if self.settings.compiler == "apple-clang" or self.settings.os == "Linux" and self.settings.compiler == "clang":
            # The Clang toolchain on Linux distros typically ships without libomp.
            self.options.provider = "llvm"
        else:
            self.options.provider = "native"

    @cached_property
    def _llvm_version(self):
        if self.settings.compiler == "clang":
            return f"[~{self.settings.compiler.version}]"
        elif self.settings.compiler == "apple-clang":
            # https://en.wikipedia.org/wiki/Xcode#Toolchain_versions
            xcode_version = Version(self.settings.compiler.version)
            if xcode_version >= "26.0":
                return "[^19.1]"
            if xcode_version >= "16.3":
                return "[^19.1]"
            if xcode_version >= "16.0":
                return "[^17]"
            if xcode_version >= "15.0":
                return "[^16]"
            if xcode_version >= "14.3":
                return "[^15]"
            if xcode_version >= "14.0":
                return "[^14]"
            if xcode_version >= "13.3":
                return "[^13]"
            if xcode_version >= "13.0":
                return "[^12]"
            if xcode_version >= "12.5":
                return "[^11]"
        elif self.settings.compiler == "msvc":
            return "[*]"
        return None

    def requirements(self):
        if self.options.provider == "llvm":
            version_range = self._llvm_version
            if version_range is None:
                raise ConanInvalidConfiguration(
                    f"No valid LLVM version could be determined for {self.settings.compiler} v{self.settings.compiler.version}"
                )
            self.requires(f"llvm-openmp/{version_range}", transitive_headers=True, transitive_libs=True)

    def package_id(self):
        self.info.clear()

    def validate(self):
        if self.options.provider == "native" and self._openmp_flags is None:
            raise ConanInvalidConfiguration(f"{self.settings.compiler} is not supported by this recipe.")

    @cached_property
    def _openmp_flags(self):
        # Based on https://github.com/Kitware/CMake/blob/v3.30.0/Modules/FindOpenMP.cmake#L119-L154
        compiler = str(self.settings.compiler)
        if compiler in {"gcc", "clang"}:
            return ["-fopenmp"]
        elif compiler == "apple-clang":
            return ["-Xpreprocessor", "-fopenmp"]
        elif compiler == "msvc":
            # Use `-o provider=llvm` for `-openmp=llvm` in MSVC.
            # TODO: add support for `-openmp=experimental`?
            return ["-openmp"]
        elif compiler == "intel-cc":
            if self.settings.compiler.mode == "classic":
                if self.settings.os == "Windows":
                    return ["-Qopenmp"]
                else:
                    return ["-qopenmp"]
            else:
                if self.settings.get_safe("compiler.frontend") == "msvc":
                    return ["-Qiopenmp"]
                else:
                    return ["-fiopenmp"]
        elif compiler == "sun-cc":
            return ["-xopenmp"]

        # The following compilers are not currently covered by settings.yml,
        # but are included for completeness.
        elif compiler == "hp":
            return ["+Oopenmp"]
        elif compiler == "pathscale":
            return ["-openmp"]
        elif compiler == "nag":
            return ["-openmp"]
        elif compiler == "absoft":
            return ["-openmp"]
        elif compiler == "nvhpc":
            return ["-mp"]
        elif compiler == "pgi":
            return ["-mp"]
        elif compiler == "xl":
            return ["-qsmp=omp"]
        elif compiler == "cray":
            return ["-h", "omp"]
        elif compiler == "fujitsu":
            return ["-Kopenmp"]
        elif compiler == "fujitsu-clang":
            return ["-fopenmp"]

        return None

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "_openmp_")

        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.includedirs = []

        if self.options.provider == "native":
            # Export appropriate flags for packages linking against this one transitively.
            # Direct dependencies of this package will rely on CMake's FindOpenMP.cmake instead.
            self.cpp_info.cflags = self._openmp_flags
            self.cpp_info.cxxflags = self._openmp_flags
            if self.settings.compiler == "msvc":
                self.cpp_info.system_libs = ["vcompd" if self.settings.build_type == "Debug" else "vcomp"]
            elif str(self.settings.compiler) in ["intel-cc", "intel-llvm"]:
                self.cpp_info.system_libs = ["iomp5"]
            else:
                self.cpp_info.sharedlinkflags = self._openmp_flags
                self.cpp_info.exelinkflags = self._openmp_flags
