import os
import textwrap

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class KissIcpConan(ConanFile):
    name = "kiss-icp"
    description = "KISS-ICP: a LiDAR odometry pipeline that just works"
    license = "MIT"
    homepage = "https://github.com/PRBonn/kiss-icp"
    topics = ("lidar", "odometry", "localization", "mapping", "slam", "robotics")
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
        self.requires("tsl-robin-map/[^1]", transitive_headers=True)
        self.requires("onetbb/[>=2021]")

    def validate(self):
        check_min_cppstd(self, 17)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.16]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        replace_in_file(self, "cpp/kiss_icp/CMakeLists.txt", "set(CMAKE_BUILD_TYPE Release)", "")
        replace_in_file(self, "cpp/kiss_icp/CMakeLists.txt", "set(CMAKE_POSITION_INDEPENDENT_CODE ON)", "")
        for module in ["core", "metrics", "pipeline"]:
            # Allow shared builds
            replace_in_file(self, f"cpp/kiss_icp/{module}/CMakeLists.txt", " STATIC", "")
            # Add missing install() commands
            save(self, f"cpp/kiss_icp/{module}/CMakeLists.txt", textwrap.dedent(f"""
                install(TARGETS kiss_icp_{module} ARCHIVE DESTINATION lib LIBRARY DESTINATION lib RUNTIME DESTINATION bin)
                install(DIRECTORY ./ DESTINATION include/kiss_icp/{module} FILES_MATCHING PATTERN "*.hpp")
            """), append=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["USE_SYSTEM_EIGEN3"] = True
        tc.cache_variables["USE_SYSTEM_SOPHUS"] = True
        tc.cache_variables["USE_SYSTEM_TSL"] = True
        tc.cache_variables["USE_SYSTEM_TBB"] = True
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder="cpp/kiss_icp")
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.components["core"].set_property("cmake_target_name", "kiss_icp_core")
        self.cpp_info.components["core"].libs = ["kiss_icp_core"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["core"].system_libs = ["m"]
        self.cpp_info.components["core"].requires = [
            "eigen::eigen",
            "sophus::sophus",
            "onetbb::onetbb",
            "tsl-robin-map::tsl-robin-map",
        ]

        self.cpp_info.components["pipeline"].set_property("cmake_target_name", "kiss_icp_pipeline")
        self.cpp_info.components["pipeline"].libs = ["kiss_icp_pipeline"]
        self.cpp_info.components["pipeline"].requires = ["core"]

        self.cpp_info.components["metrics"].set_property("cmake_target_name", "kiss_icp_metrics")
        self.cpp_info.components["metrics"].libs = ["kiss_icp_metrics"]
        self.cpp_info.components["metrics"].requires = ["eigen::eigen"]
