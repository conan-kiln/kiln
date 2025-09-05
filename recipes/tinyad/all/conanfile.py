import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class TinyADConan(ConanFile):
    name = "tinyad"
    homepage = "https://github.com/patr-schm/TinyAD"
    description = "TinyAD is a C++ header-only library for second-order automatic differentiation"
    topics = ("algebra", "linear-algebra", "optimization", "autodiff", "numerical", "header-only")
    package_type = "header-library"
    license = "MIT"
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("eigen/3.4.0")

    @property
    def _compilers_minimum_version(self):
        return {
            "gcc": "7",
            "clang": "7",
            "apple-clang": "12.0",
            "msvc": "191",
        }

    def validate(self):
        required_min_cppstd = "17"
        check_min_cppstd(self, required_min_cppstd)

        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if minimum_version and Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(
                f"{self.ref} requires C++{required_min_cppstd}, which your compiler does not support."
            )

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        # The project has a CMakelists.txt file, but it doesn't have "install" logic
        # so we just copy the headers to the package folder
        copy(self, "include/**", src=self.source_folder, dst=self.package_folder)
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "TinyAD")
        self.cpp_info.set_property("cmake_target_name", "TinyAD")

        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []

        if is_msvc(self):
            # https://github.com/patr-schm/TinyAD/blob/29417031c185b6dc27b6d4b684550d844459b735/CMakeLists.txt#L35
            self.cpp_info.cxxflags.append("/bigobj")
