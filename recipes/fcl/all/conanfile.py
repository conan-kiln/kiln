import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, CMakeDeps, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class FclConan(ConanFile):
    name = "fcl"
    description = "C++11 library for performing three types of proximity " \
                  "queries on a pair of geometric models composed of triangles."
    license = "BSD-3-Clause"
    topics = ("geometry", "collision")
    homepage = "https://github.com/flexible-collision-library/fcl"

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_octomap": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_octomap": True,
    }
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        # Used in fcl/common/types.h public header
        self.requires("eigen/3.4.0", transitive_headers=True)
        # Used in fcl/narrowphase/detail/convexity_based_algorithm/support.h
        self.requires("libccd/2.1", transitive_headers=True)
        if self.options.with_octomap:
            # Used in fcl/geometry/octree/octree.h
            self.requires("octomap/1.9.7", transitive_headers=True)

    def validate(self):
        check_min_cppstd(self, 11)
        if self.settings.os == "Windows" and self.options.shared:
            raise ConanInvalidConfiguration(f"{self.ref} doesn't properly support shared lib on Windows")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["FCL_ENABLE_PROFILING"] = False
        tc.cache_variables["FCL_TREAT_WARNINGS_AS_ERRORS"] = False
        tc.cache_variables["FCL_HIDE_ALL_SYMBOLS"] = False
        tc.cache_variables["FCL_STATIC_LIBRARY"] = not self.options.shared
        tc.cache_variables["FCL_USE_X64_SSE"] = False # Let consumer decide to add relevant compile options, fcl doesn't have simd intrinsics
        tc.cache_variables["FCL_USE_HOST_NATIVE_ARCH"] = False
        tc.cache_variables["FCL_USE_SSE"] = False
        tc.cache_variables["FCL_COVERALLS"] = False
        tc.cache_variables["FCL_COVERALLS_UPLOAD"] = False
        tc.cache_variables["FCL_WITH_OCTOMAP"] = self.options.with_octomap
        if self.options.with_octomap:
            octomap_version_str = str(self.dependencies["octomap"].ref.version)
            tc.cache_variables["OCTOMAP_VERSION"] = octomap_version_str
            octomap_version = Version(octomap_version_str)
            tc.cache_variables["OCTOMAP_MAJOR_VERSION"] = str(octomap_version.major)
            tc.cache_variables["OCTOMAP_MINOR_VERSION"] = str(octomap_version.minor)
            tc.cache_variables["OCTOMAP_PATCH_VERSION"] = str(octomap_version.patch)
        tc.cache_variables["BUILD_TESTING"] = False
        tc.cache_variables["FCL_NO_DEFAULT_RPATH"] = False
        tc.generate()

        cd = CMakeDeps(self)
        cd.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "CMake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "fcl")
        self.cpp_info.set_property("cmake_target_name", "fcl")
        self.cpp_info.set_property("pkg_config_name", "fcl")
        self.cpp_info.libs = ["fcl"]
