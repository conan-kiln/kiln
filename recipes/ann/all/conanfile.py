import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class AnnConan(ConanFile):
    name = "ann"
    description = (
        "ANN is a library written in C++, which supports data structures and "
        "algorithms for both exact and approximate nearest neighbor searching "
        "in arbitrarily high dimensions."
    )
    license = "LGPL-2.1-or-later"
    homepage = "https://www.cs.umd.edu/~mount/ANN"
    topics = ("nns", "nearest-neighbor-search")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        copy(self, "CMakeLists.txt", src=self.recipe_folder, dst=self.export_sources_folder)
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["ANN_SRC_DIR"] = self.source_folder.replace("\\", "/")
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder="..")
        cmake.build()

    def package(self):
        for license_file in ("Copyright.txt", "License.txt"):
            copy(self, license_file, src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["ANN"]
        if self.settings.os == "Windows" and not self.options.shared:
            self.cpp_info.defines.append("ANN_STATIC")
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("m")
