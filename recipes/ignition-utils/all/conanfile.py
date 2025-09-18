import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class IgnitionUtilsConan(ConanFile):
    name = "ignition-utils"
    description = "Provides general purpose classes and functions designed for robotic applications."
    license = "Apache-2.0"
    homepage = "https://gazebosim.org/libs/utils"
    topics = ("ignition", "robotics", "utils", "gazebo")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "ign_utils_vendor_cli11": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "ign_utils_vendor_cli11": True,
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("ignition-cmake/[^2.17.1]", visible=False)
        if self.options.ign_utils_vendor_cli11:
            self.requires("cli11/[^2.4.2]")

    def validate(self):
        check_min_cppstd(self, 17)

    def build_requirements(self):
        self.tool_requires("ignition-cmake/<host_version>")
        if self.settings_build.os == "Windows":
            # For sed
            self.win_bash = True
            if not self.conf.get("tools.microsoft.bash:path", check_type=str):
                self.tool_requires("msys2/latest")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        replace_in_file(self, "CMakeLists.txt", "${CMAKE_SOURCE_DIR}", "${PROJECT_SOURCE_DIR}")
        replace_in_file(self, "CMakeLists.txt", "${CMAKE_BINARY_DIR}", "${PROJECT_BINARY_DIR}")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_TESTING"] = False
        tc.variables["IGN_UTILS_VENDOR_CLI11"] = self.options.ign_utils_vendor_cli11
        tc.variables["CMAKE_FIND_DEBUG_MODE"] = True
        tc.variables["CMAKE_DISABLE_FIND_PACKAGE_Doxygen"] = True
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*.hpp",
             os.path.join(self.source_folder, "cli/include/ignition/utils/cli"),
             os.path.join(self.package_folder, "include/ignition/utils1/ignition/utils/cli"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

        # Remove MS runtime files
        for dll_pattern_to_remove in ["concrt*.dll", "msvcp*.dll", "vcruntime*.dll"]:
            rm(self, dll_pattern_to_remove, os.path.join(self.package_folder, "bin"), recursive=True)

    def package_info(self):
        version_major = Version(self.version).major
        lib_name = f"ignition-utils{version_major}"

        self.cpp_info.set_property("cmake_file_name", lib_name)
        self.cpp_info.set_property("cmake_target_name", f"{lib_name}::{lib_name}")

        main_component = self.cpp_info.components[lib_name]
        main_component.libs = [lib_name]
        main_component.includedirs.append(f"include/ignition/utils{version_major}")
        if self.options.ign_utils_vendor_cli11:
            main_component.requires.append("cli11::cli11")

        cli_component = self.cpp_info.components["cli"]
        cli_component.includedirs.append(f"include/ignition/utils{version_major}/ignition/utils")
        if self.options.ign_utils_vendor_cli11:
            cli_component.requires.append("cli11::cli11")
