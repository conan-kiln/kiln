import os
import textwrap

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class MapClosuresConan(ConanFile):
    name = "map_closures"
    description = "Effectively Detecting Loop Closures using Point Cloud Density Maps"
    license = "MIT"
    homepage = "https://github.com/PRBonn/MapClosures"
    topics = ("lidar", "loop-closure", "mapping", "slam", "robotics")
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
        copy(self, "conan_deps.cmake", self.recipe_folder, os.path.join(self.export_sources_folder, "src", "cpp"))

    def config_options(self):
        if self.settings.os == "Windows":
            self.package_type = "static-library"
            del self.options.shared
            del self.options.fPIC

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("eigen/[>=3.3 <6]", transitive_headers=True)
        self.requires("opencv/[^4]", transitive_headers=True, transitive_libs=True)
        self.requires("sophus/[^1]")
        self.requires("srrg_hbst/[*]", transitive_headers=True)

    def validate(self):
        check_min_cppstd(self, 17)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.16]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        rmdir(self, "cpp/3rdparty")
        replace_in_file(self, "cpp/CMakeLists.txt", "include(3rdparty/find_dependencies.cmake)", "")
        replace_in_file(self, "cpp/CMakeLists.txt", "set(CMAKE_BUILD_TYPE Release)", "")
        replace_in_file(self, "cpp/CMakeLists.txt", "set(CMAKE_POSITION_INDEPENDENT_CODE ON)", "")
        # Allow shared builds
        replace_in_file(self, "cpp/map_closures/CMakeLists.txt", "add_library(map_closures STATIC)", "add_library(map_closures)")
        # Add missing install() commands
        save(self, "cpp/map_closures/CMakeLists.txt", textwrap.dedent("""\
            install(TARGETS map_closures ARCHIVE DESTINATION lib LIBRARY DESTINATION lib RUNTIME DESTINATION bin)
            install(DIRECTORY ./ DESTINATION include/map_closures FILES_MATCHING PATTERN "*.hpp")
        """), append=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["CMAKE_PROJECT_map_closures_cpp_INCLUDE"] = "conan_deps.cmake"
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder="cpp")
        cmake.build()

    def package(self):
        copy(self, "LICENSE*", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["map_closures"]
        self.cpp_info.defines = [
            "SRRG_HBST_HAS_EIGEN",
            "SRRG_HBST_HAS_OPENCV",
            "SRRG_MERGE_DESCRIPTORS",
        ]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]
        self.cpp_info.requires = [
            "eigen::eigen",
            "opencv::opencv_core",
            "opencv::opencv_features2d",
            "sophus::sophus",
            "srrg_hbst::srrg_hbst",
        ]
