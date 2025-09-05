import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class NormConan(ConanFile):
    name = "norm"
    description = "A reliable multicast transport protocol"
    topics = ("multicast", "transport protocol", "nack-oriented reliable multicast")
    homepage = "https://www.nrl.navy.mil/itd/ncs/products/norm"
    license = "NRL"
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
        self.requires("libxml2/[^2.12.5]") # dependency of protolib actually

    def source(self):
        get(self, **self.conan_data["sources"][self.version])
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["NORM_CUSTOM_PROTOLIB_VERSION"] = "./protolib" # FIXME: use external protolib when available in CCI
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        if self.options.shared:
            rm(self, "*proto*", os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "norm")
        self.cpp_info.set_property("cmake_target_name", "norm::norm")
        self.cpp_info.libs = ["norm"]
        if not self.options.shared:
            self.cpp_info.libs.append("protokit")

        if self.settings.os == "Windows" and self.options.shared:
            self.cpp_info.defines.append("NORM_USE_DLL")

        if self.settings.os == "Windows":
            # system libs of protolib actually
            self.cpp_info.system_libs.extend(["ws2_32", "iphlpapi", "user32", "gdi32", "advapi32", "ntdll"])
        elif self.settings.os == "Linux":
            self.cpp_info.system_libs.extend(["dl", "rt"])
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("pthread")
