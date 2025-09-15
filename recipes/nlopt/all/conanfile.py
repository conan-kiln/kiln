import os

from conan import ConanFile
from conan.tools.build import stdcpp_library
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.4"


class NloptConan(ConanFile):
    name = "nlopt"
    description = "Library for nonlinear optimization, wrapping many " \
                  "algorithms for global and local, constrained or " \
                  "unconstrained, optimization."
    license = "MIT"
    topics = ("optimization", "nonlinear")
    homepage = "https://github.com/stevengj/nlopt"
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "cxx": [True, False],
        "enable_luksan_solvers": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "cxx": True,
        "enable_luksan_solvers": True,  # LGPL
    }
    implements = ["auto_shared_fpic"]

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if not self.options.cxx:
            self.languages = ["C"]
        if self.options.enable_luksan_solvers:
            self.license = "MIT AND LGPL-2.1-or-later"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["NLOPT_CXX"] = self.options.cxx
        tc.variables["NLOPT_LUKSAN"] = self.options.enable_luksan_solvers
        tc.variables["NLOPT_FORTRAN"] = False
        tc.variables["NLOPT_PYTHON"] = False
        tc.variables["NLOPT_OCTAVE"] = False
        tc.variables["NLOPT_MATLAB"] = False
        tc.variables["NLOPT_GUILE"] = False
        tc.variables["NLOPT_SWIG"] = False
        tc.variables["NLOPT_TESTS"] = False
        tc.variables["WITH_THREADLOCAL"] = True
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*/COPYING", os.path.join(self.source_folder, "src/algs"), os.path.join(self.package_folder, "licenses"), keep_path=True)
        copy(self, "*/COPYRIGHT", os.path.join(self.source_folder, "src/algs"), os.path.join(self.package_folder, "licenses"), keep_path=True)
        if not self.options.enable_luksan_solvers:
            rmdir(self, os.path.join(self.package_folder, "licenses", "luksan"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        rm(self, "*.pdb", os.path.join(self.package_folder, "bin"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "NLopt")
        self.cpp_info.set_property("cmake_target_name", "NLopt::nlopt")
        self.cpp_info.set_property("pkg_config_name", "nlopt")
        self.cpp_info.libs = ["nlopt"]
        if self.settings.os == "Windows" and self.options.shared:
            self.cpp_info.defines.append("NLOPT_DLL")
        if not self.options.shared:
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.system_libs = ["m"]
            if self.options.cxx and stdcpp_library(self):
                self.cpp_info.system_libs.append(stdcpp_library(self))
