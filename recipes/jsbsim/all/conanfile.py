import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class JsbsimConan(ConanFile):
    name = "jsbsim"
    description = (
        "JSBSim is a multi-platform, general purpose object-oriented "
        "Flight Dynamics Model (FDM) written in C++"
    )
    license = "LGPL-2.1-or-later"
    topics = ("aircraft", "aerospace", "flight-dynamics", "flight-simulation")
    homepage = "https://github.com/JSBSim-Team/jsbsim"
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
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("expat/[>=2.6.2 <3]")

    def validate(self):
        check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["SYSTEM_EXPAT"] = True
        tc.variables["BUILD_DOCS"] = False
        tc.variables["BUILD_PYTHON_MODULE"] = False
        tc.generate()
        deps = CMakeDeps(self)
        deps.set_property("expat", "cmake_file_name", "EXPAT")
        deps.set_property("expat", "cmake_target_name", "EXPAT::EXPAT")
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "JSBSim")
        self.cpp_info.libs = ["JSBSim"]
        self.cpp_info.includedirs = [os.path.join("include", "JSBSim")]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("m")
        elif self.settings.os == "Windows":
            self.cpp_info.system_libs.extend(["wsock32", "ws2_32"])
            if not self.options.shared:
                self.cpp_info.defines.append("JSBSIM_STATIC_LINK")
