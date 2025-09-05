import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc

required_conan_version = ">=2.1"


class CpuinfoConan(ConanFile):
    name = "cpuinfo"
    description = "cpuinfo is a library to detect essential for performance " \
                  "optimization information about host CPU."
    license = "BSD-2-Clause"
    topics = ("cpu", "cpuid", "cpu-cache", "cpu-model", "instruction-set", "cpu-topology")
    homepage = "https://github.com/pytorch/cpuinfo"
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "log_level": ["default", "debug", "info", "warning", "error", "fatal", "none"],
        "tools": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "log_level": "default",
        "tools": False,
    }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if is_msvc(self):
            # Only static for msvc
            # Injecting CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS is not sufficient since there are global symbols
            del self.options.shared
            self.package_type = "static-library"
        if self.options.get_safe("shared"):
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        rmdir(self, "deps")
        replace_in_file(self, "CMakeLists.txt",
                        "CMAKE_MINIMUM_REQUIRED(VERSION 3.5 FATAL_ERROR)",
                        "CMAKE_MINIMUM_REQUIRED(VERSION 3.5 FATAL_ERROR)")
        # Fix install dir of dll
        replace_in_file(self, "CMakeLists.txt",
                        "LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}",
                        "LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR} RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}")

    def generate(self):
        tc = CMakeToolchain(self)
        # cpuinfo
        tc.cache_variables["CPUINFO_LIBRARY_TYPE"] = "default"
        tc.cache_variables["CPUINFO_RUNTIME_TYPE"] = "default"
        tc.cache_variables["CPUINFO_LOG_LEVEL"] = self.options.log_level
        tc.cache_variables["CPUINFO_BUILD_TOOLS"] = self.options.tools
        tc.cache_variables["CPUINFO_BUILD_UNIT_TESTS"] = False
        tc.cache_variables["CPUINFO_BUILD_MOCK_TESTS"] = False
        tc.cache_variables["CPUINFO_BUILD_BENCHMARKS"] = False
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "cpuinfo")
        self.cpp_info.set_property("pkg_config_name", "libcpuinfo")

        self.cpp_info.components["cpuinfo"].set_property("cmake_target_name", "cpuinfo::cpuinfo")
        self.cpp_info.components["cpuinfo"].libs = ["cpuinfo"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["cpuinfo"].system_libs.append("pthread")

        if self.settings.os == "Android":
            self.cpp_info.components["cpuinfo"].system_libs.append("log")
