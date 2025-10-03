import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd, check_max_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc

required_conan_version = ">=2.1"


class EmbagConan(ConanFile):
    name = "embag"
    description = "Schema and dependency free ROS bag reader"
    license = "MIT"
    homepage = "https://github.com/embarktrucks/embag"
    topics = ("rosbag", "ros", "robotics")
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
        copy(self, "CMakeLists.txt", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("boost/[^1.74.0]", transitive_headers=True, options={"with_iostreams": True})
        self.requires("lz4/[^1.9.4]", transitive_headers=True)
        self.requires("bzip2/[^1.0.8]", transitive_headers=True)
        self.requires("span-lite/[*]", transitive_headers=True)

    def validate(self):
        check_min_cppstd(self, 14)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        os.unlink("lib/span.hpp")
        for f in [
            "lib/ros_message.h",
            "lib/message_parser.h",
            "lib/ros_value.h",
        ]:
            replace_in_file(self, f, "span.hpp", "nonstd/span.hpp")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["embag"]

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]
        if is_msvc(self):
            # For a #if __cplusplus < 201402L check in lib/util.h, which is a public header
            self.cpp_info.cxxflags.append("/Zc:__cplusplus")
