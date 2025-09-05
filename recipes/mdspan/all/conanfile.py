import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"

class MDSpanConan(ConanFile):
    name = "mdspan"
    description = "Production-quality reference implementation of mdspan"
    license = "BSD-3-Clause"
    homepage = "https://github.com/kokkos/mdspan"
    topics = ("multi-dimensional", "array", "span", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    @property
    def _min_cppstd(self):
        return "14" if Version(self.version) < "0.6.0" else "17"

    @property
    def _minimum_compilers_version(self):
        return {
            "14": {
                "msvc": "191" if Version(self.version) < "0.2.0" else "192",
                "gcc": "5",
                "clang": "3.4",
                "apple-clang": "5.1"
            },
            "17": {
                "msvc": "192",
                "gcc": "8",
                "clang": "7",
                "apple-clang": "12",
            }
        }.get(self._min_cppstd, {})

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def validate(self):
        check_min_cppstd(self, self._min_cppstd)
        min_version = self._minimum_compilers_version.get(
            str(self.settings.compiler))
        if not min_version:
            self.output.warning(f"{self.ref} recipe lacks information about the {self.settings.compiler} "
                                "compiler support.")
        else:
            if Version(self.settings.compiler.version) < min_version:
                raise ConanInvalidConfiguration(
                    f"{self.ref} requires C++{self._min_cppstd} support. "
                    f"The current compiler {self.settings.compiler} {self.settings.compiler.version} does not support it.")

        # TODO: check msvcc version more precisely
        if self.settings.compiler == "msvc" and Version(self.settings.compiler.version) == "192":
            raise ConanInvalidConfiguration(
                "Unsupported MSVC version due to upstream bug. The supported MSVC versions are (< 192 or 193 <=)."
                "See upstream issue https://github.com/kokkos/mdspan/issues/26 for details.")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, pattern="*LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        copy(
            self,
            pattern="*",
            dst=os.path.join(self.package_folder, "include"),
            src=os.path.join(self.source_folder, "include"),
        )

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []

        self.cpp_info.set_property("cmake_file_name", "mdspan")
        self.cpp_info.set_property("cmake_target_name", "std::mdspan")
