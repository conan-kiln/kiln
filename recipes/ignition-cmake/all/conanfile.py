import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class IgnitionCmakeConan(ConanFile):
    name = "ignition-cmake"
    description = "A set of CMake modules that are used by the C++-based Ignition projects."
    license = "Apache-2.0"
    homepage = "https://github.com/gazebosim/gz-cmake"
    topics = ("ignition", "robotics", "cmake", "gazebo", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_INSTALL_DATAROOTDIR"] = "lib"
        tc.variables["SKIP_component_name"] = False
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "bin"))

        version_major = Version(self.version).major
        cmake_config_files_dir = os.path.join(self.package_folder, "lib", "cmake", f"ignition-cmake{version_major}")
        for file in os.listdir(cmake_config_files_dir):
            if file.endswith(".cmake"):
                if file == f"ignition-cmake{version_major}-utilities-targets.cmake":
                    # retain the special config file for utilities target provided by ignition-cmake
                    continue
                os.remove(os.path.join(cmake_config_files_dir, file))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []

        version_major = Version(self.version).major
        ign_cmake_component = f"ignition-cmake{version_major}"
        self.cpp_info.set_property("cmake_file_name", ign_cmake_component)

        base_module_path = os.path.join("lib", "cmake", ign_cmake_component)
        ign_cmake_file = os.path.join(base_module_path, f"cmake{version_major}", "IgnCMake.cmake")
        utils_targets_file = os.path.join(base_module_path, f"{ign_cmake_component}-utilities-targets.cmake")
        self.cpp_info.set_property("cmake_build_modules", [ign_cmake_file, utils_targets_file])

        self.cpp_info.components[ign_cmake_component].set_property("cmake_target_name", f"{ign_cmake_component}::{ign_cmake_component}")
        self.cpp_info.components[ign_cmake_component].builddirs.append(os.path.join(base_module_path, f"cmake{version_major}"))

        self.cpp_info.components["utilities"].set_property("cmake_target_name", f"{ign_cmake_component}::utilities")
        self.cpp_info.components["utilities"].builddirs.append(os.path.join(base_module_path, f"cmake{version_major}"))
        self.cpp_info.components["utilities"].includedirs.append(os.path.join("include", "ignition", f"cmake{version_major}"))
