import os
import textwrap

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class RkoLioConan(ConanFile):
    name = "rko_lio"
    description = "A Robust Approach for LiDAR-Inertial Odometry Without Sensor-Specific Modelling"
    license = "MIT"
    homepage = "https://github.com/PRBonn/rko_lio"
    topics = ("lidar", "imu", "odometry", "localization", "mapping", "slam", "robotics")
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

    def config_options(self):
        if self.settings.os == "Windows":
            self.package_type = "static-library"
            del self.options.shared
            del self.options.fPIC

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("eigen/[>=3.3 <6]", transitive_headers=True)
        self.requires("sophus/[^1.22]", transitive_headers=True)
        self.requires("bonxai/[>=0.3 <1]", transitive_headers=True)
        self.requires("onetbb/[>=2021]")
        self.requires("nlohmann_json/[^3.11]")

    def validate(self):
        check_min_cppstd(self, 20)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.22]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        save(self, "cmake/dependencies.cmake", "")
        # Allow Eigen 5.0.0
        replace_in_file(self, "CMakeLists.txt", "Eigen3 3.4", "Eigen3")
        # Allow shared builds
        replace_in_file(self, "cpp/rko_lio/core/CMakeLists.txt",
                        "add_library(rko_lio.core STATIC)",
                        "add_library(rko_lio.core)")
        # Add missing install() commands
        save(self, "cpp/rko_lio/core/CMakeLists.txt", textwrap.dedent("""\
            install(TARGETS rko_lio.core ARCHIVE DESTINATION lib LIBRARY DESTINATION lib RUNTIME DESTINATION bin)
            install(DIRECTORY ./ DESTINATION include/rko_lio FILES_MATCHING PATTERN "*.hpp")
        """), append=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["RKO_LIO_BUILD_ROS"] = False
        tc.generate()
        deps = CMakeDeps(self)
        deps.set_property("bonxai", "cmake_file_name", "Bonxai")
        deps.set_property("bonxai::bonxai_core", "cmake_target_name", "bonxai_core")
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
        self.cpp_info.libs = ["rko_lio.core"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]
