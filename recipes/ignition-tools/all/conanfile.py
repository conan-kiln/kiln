import os
from pathlib import Path

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class IgnitionToolsConan(ConanFile):
    name = "ignition-tools"
    description = "Ignition entry point for using all the suite of ignition tools."
    license = "Apache-2.0"
    homepage = "https://ignitionrobotics.org/libs/tools"
    topics = ("ignition", "robotics", "tools", "gazebo")
    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler

    def requirements(self):
        self.requires("backward-cpp/[^1.6]")

    def validate(self):
        check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        replace_in_file(self, "CMakeLists.txt",
                        "cmake_minimum_required(VERSION 2.8.12 FATAL_ERROR)",
                        "cmake_minimum_required(VERSION 3.5)")
        for cmakelists in Path(self.source_folder).rglob("CMakeLists.txt"):
            replace_in_file(self, cmakelists, "${CMAKE_SOURCE_DIR}", "${PROJECT_SOURCE_DIR}", strict=False)
            replace_in_file(self, cmakelists, "${CMAKE_BINARY_DIR}", "${PROJECT_BINARY_DIR}", strict=False)
        # Generating ign.rb fails on Windows, do it outside of CMake in package() instead
        replace_in_file(self, "src/CMakeLists.txt",
                        "# Two steps to create `ign`",
                        "return() #")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["USE_SYSTEM_BACKWARDCPP"] = True
        tc.cache_variables["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = True
        tc.cache_variables["BUILD_TESTING"] = False
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    @staticmethod
    def _chmod_plus_x(filename):
        if os.name == "posix":
            os.chmod(filename, os.stat(filename).st_mode | 0o111)

    def package(self):
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()

        # Generate ign.rb
        ign_rb_content = load(self, os.path.join(self.source_folder, "src", "ign.in"))
        ign_rb_content = ign_rb_content.replace(
            "'@CMAKE_INSTALL_PREFIX@/share/ignition/'",
            "File.expand_path('../share/ignition/', __dir__)"
        )
        ign_rb_content = ign_rb_content.replace("@ENV_PATH_DELIMITER@", os.pathsep)
        suffix = ".rb" if self.settings.os == "Windows" else ""
        ign_rb_path = os.path.join(self.package_folder, "bin", f"ign{suffix}")
        save(self, ign_rb_path, ign_rb_content)
        self._chmod_plus_x(ign_rb_path)

        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

        # Remove MS runtime files
        for dll_pattern_to_remove in ["concrt*.dll", "msvcp*.dll", "vcruntime*.dll"]:
            rm(self, dll_pattern_to_remove, os.path.join(self.package_folder, "bin"), recursive=True)

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "ignition-tools")
        self.cpp_info.set_property("pkg_config_name", "ignition-tools")
        self.cpp_info.includedirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = ["share"]

        # The package builds an ignition-tools-backward wrapper library,
        # but it's only meant to be used as a runtime dependency of the ign script
