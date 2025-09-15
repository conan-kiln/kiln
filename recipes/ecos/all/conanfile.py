import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.4"


class EcosConan(ConanFile):
    name = "ecos"
    description = "ECOS is a numerical software for solving convex second-order cone programs (SOCPs)."
    license = "GPL-3.0-or-later"
    topics = ("ecos", "conic-solver")
    homepage = "https://github.com/embotech/ecos"
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "use_long": [True, False],
    }
    default_options = {
        "use_long": True,
    }
    languages = ["C"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        # Uses a modified version of suitesparse-ldl, which cannot be unvendored
        pass

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["USE_LONG"] = self.options.use_long
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "ecos")
        self.cpp_info.set_property("cmake_target_name", "ecos::ecos")
        self.cpp_info.libs = ["ecos"]
        self.cpp_info.defines.append("CTRLC=1")
        if self.options.use_long:
            self.cpp_info.defines.extend(["LDL_LONG", "DLONG"])
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("m")
