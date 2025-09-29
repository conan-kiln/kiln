import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class Gm2calcConan(ConanFile):
    name = "gm2calc"
    description = "C++ library to calculate the anomalous magnetic moment of the muon in the MSSM and 2HDM"
    license = "GPL-3.0"
    homepage = "https://github.com/GM2Calc/GM2Calc"
    topics = ("high-energy", "physics", "hep", "magnetic moment", "muon", "mssm", "2hdm")
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

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("boost/[^1.71.0]")
        self.requires("eigen/3.4.0", transitive_headers=True)

    def validate(self):
        check_min_cppstd(self, 14)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # Fix src/slhaea.h:25:10: fatal error: boost/algorithm/string/classification.hpp: No such file or directory
        save(self, "src/CMakeLists.txt", "\ninclude_directories(${Boost_INCLUDE_DIRS})", append=True)
        # Disable examples, test and doc
        for subdir in ["examples", "test", "doc"]:
            replace_in_file(self, "CMakeLists.txt", f"add_subdirectory({subdir})", "")


    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = True
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "GM2Calc")
        self.cpp_info.set_property("cmake_target_name", "GM2Calc::GM2Calc")
        self.cpp_info.set_property("pkg_config_name", "gm2calc")
        self.cpp_info.libs = ["gm2calc"]
