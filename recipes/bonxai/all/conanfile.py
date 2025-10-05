import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class BonxaiConan(ConanFile):
    name = "bonxai"
    description = "Compact hierarchical data structure for sparse volumetric voxel grids"
    license = "MPL-2.0"
    homepage = "https://github.com/facontidavide/Bonxai"
    topics = ("voxel-grid", "sparse-data-structure", "3d-mapping", "vdb", "robotics")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "header_only": [True, False],
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "header_only": True,
        "shared": False,
        "fPIC": True,
    }
    implements = ["auto_shared_fpic", "auto_header_only"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if not self.options.header_only:
            self.requires("eigen/[>=3.3 <6]", transitive_headers=True)
            self.requires("pcl/[^1.13]")

    def validate(self):
        check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        replace_in_file(self, "bonxai_map/include/bonxai_map/pcl_utils.hpp", "eigen3/Eigen", "Eigen")
        replace_in_file(self, "bonxai_map/include/bonxai_map/probabilistic_map.hpp", "eigen3/Eigen", "Eigen")
        replace_in_file(self, "bonxai_map/src/probabilistic_map.cpp", "eigen3/Eigen", "Eigen")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_MAP"] = not self.options.header_only
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
        self.cpp_info.components["bonxai_core"].bindirs = []
        self.cpp_info.components["bonxai_core"].libdirs = []

        if not self.options.header_only:
            self.cpp_info.components["bonxai_map"].libs = ["bonxai_map"]
            self.cpp_info.components["bonxai_map"].requires = [
                "bonxai_core",
                "eigen::eigen",
                "pcl::common",
                "pcl::io",
                "pcl::filters",
            ]
