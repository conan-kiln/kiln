import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.4"


class HdrhistogramcConan(ConanFile):
    name = "hdrhistogram-c"
    license = ("BSD-2-Clause", "CC0-1.0")
    homepage = "https://github.com/HdrHistogram/HdrHistogram_c"
    description = "'C' port of High Dynamic Range (HDR) Histogram"
    topics = ("libraries", "c", "histogram")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "fPIC": [True, False],
        "shared": [True, False],
    }
    default_options = {
        "fPIC": True,
        "shared": False,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("zlib-ng/[^2.0]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["HDR_HISTOGRAM_BUILD_PROGRAMS"] = False
        tc.variables["HDR_HISTOGRAM_BUILD_SHARED"] = self.options.shared
        tc.variables["HDR_HISTOGRAM_INSTALL_SHARED"] = self.options.shared
        tc.variables["HDR_HISTOGRAM_BUILD_STATIC"] = not self.options.shared
        tc.variables["HDR_HISTOGRAM_INSTALL_STATIC"] = not self.options.shared
        tc.variables["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = self.options.shared
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        copy(self, "LICENSE.txt", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        copy(self, "COPYING.txt", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        target = "hdr_histogram" if self.options.shared else "hdr_histogram_static"
        self.cpp_info.set_property("cmake_file_name", "hdr_histogram")
        self.cpp_info.set_property("cmake_target_name", f"hdr_histogram::{target}")
        if Version(self.version) >= "0.11.6":
            self.cpp_info.set_property("pkg_config_name", "hdr_histogram")

        self.cpp_info.libs = collect_libs(self)
        self.cpp_info.includedirs.append(os.path.join("include", "hdr"))
        if not self.options.shared:
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.system_libs = ["m", "rt", "pthread"]
            elif self.settings.os == "Windows":
                self.cpp_info.system_libs = ["ws2_32"]
