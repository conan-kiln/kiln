import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import *

required_conan_version = ">=2.4"


class ApriltagConan(ConanFile):
    name = "apriltag"
    description = ("AprilTag is a visual fiducial system, useful for a wide variety of tasks"
                   " including augmented reality, robotics, and camera calibration")
    homepage = "https://april.eecs.umich.edu/software/apriltag"
    topics = ("robotics", "computer-vision", "augmented-reality", "camera-calibration")
    license = "BSD-2-Clause"
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
    languages = ["C"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.16 <5]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        VirtualBuildEnv(self).generate()
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_EXAMPLES"] = False
        tc.variables["BUILD_PYTHON_WRAPPER"] = False
        if self.settings.os == "Windows":
            tc.preprocessor_definitions["NOMINMAX"] = ""
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE.md", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "apriltag")
        self.cpp_info.set_property("cmake_target_name", "apriltag::apriltag")
        self.cpp_info.set_property("pkg_config_name", "apriltag")
        suffix = "d" if self.settings.build_type == "Debug" else ""
        self.cpp_info.libs = ["apriltag" + suffix]
        self.cpp_info.includedirs.append(os.path.join("include", "apriltag"))
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m", "pthread"]
        elif self.settings.os == "Windows":
            self.cpp_info.system_libs = ["winmm"]
            self.cpp_info.defines.append("NOMINMAX")
