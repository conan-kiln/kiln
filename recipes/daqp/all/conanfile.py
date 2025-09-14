import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class DaqpConan(ConanFile):
    name = "daqp"
    description = "DAQP is a dual active-set solver for convex quadratic programming"
    license = "MIT"
    homepage = "https://github.com/darnstrom/daqp"
    topics = ("optimization", "quadratic-programming", "active-set", "solver")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "soft_weights": [True, False],
        "with_eigen": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "soft_weights": False,
        "with_eigen": True,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_eigen:
            self.requires("eigen/3.4.0", transitive_headers=True)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        replace_in_file(self, "CMakeLists.txt", "set(CMAKE_POSITION_INDEPENDENT_CODE ON)", "")
        replace_in_file(self, "CMakeLists.txt", "target_link_libraries(daqpstat daqp)", "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["TEST"] = False
        tc.cache_variables["PROFILING"] = False
        tc.cache_variables["MATLAB"] = False
        tc.cache_variables["JULIA"] = False
        tc.cache_variables["EIGEN"] = self.options.with_eigen
        tc.cache_variables["SOFT_WEIGHTS"] = self.options.soft_weights
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def _patch_sources(self):
        cmakelists = os.path.join(self.source_folder, "CMakeLists.txt")
        if self.options.shared:
            replace_in_file(self, cmakelists, "install(TARGETS daqpstat ", "message(TRACE ")
            save(self, cmakelists, "\nset_target_properties(daqpstat PROPERTIES EXCLUDE_FROM_ALL 1)\n", append=True)
        else:
            replace_in_file(self, cmakelists, "install(TARGETS daqp ", "message(TRACE ")
            save(self, cmakelists, "\nset_target_properties(daqp PROPERTIES EXCLUDE_FROM_ALL 1)\n", append=True)

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE*", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "daqp")
        self.cpp_info.set_property("cmake_target_name", "daqp")
        self.cpp_info.set_property("cmake_target_aliases", ["daqpstat"])
        self.cpp_info.libs = ["daqp" if self.options.shared else "daqpstat"]
        self.cpp_info.includedirs = ["include"]
        if self.options.soft_weights:
            self.cpp_info.defines.append("SOFT_WEIGHTS")
        if not self.options.shared:
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.system_libs = ["m"]
