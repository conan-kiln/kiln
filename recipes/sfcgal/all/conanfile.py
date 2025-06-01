import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class SfcgalConan(ConanFile):
    name = "sfcgal"
    description = ("SFCGAL is a C++ wrapper library around CGAL with the aim of supporting"
                   " ISO 191007:2013 and OGC Simple Features for 3D operations.")
    license = "LGPL-2.0-only"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://sfcgal.gitlab.io/SFCGAL"
    topics = ("spatial", "3d", "geometry", "gis")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_osg": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_osg": False,
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("cgal/[^5.6]", transitive_headers=True, transitive_libs=True)
        self.requires("boost/[^1.71.0]")
        if self.options.with_osg:
            self.requires("openscenegraph/3.6.5")

    def validate(self):
        check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # CMake v4 support
        replace_in_file(self, "CMakeLists.txt",
                        "cmake_minimum_required( VERSION 2.8 )",
                        "cmake_minimum_required( VERSION 3.5 )")
        replace_in_file(self, "CMakeLists.txt", 'add_definitions( "-fPIC" )', "")
        # CGAL::CGAL_Core is redundant, already covered by CGAL::CGAL
        replace_in_file(self, "src/CMakeLists.txt", " CGAL::CGAL_Core", "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["SFCGAL_WITH_OSG"] = self.options.with_osg
        tc.variables["Boost_MAJOR_VERSION"] = 1
        tc.variables["Boost_MINOR_VERSION"] = Version(self.dependencies["boost"].ref.version).minor
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

        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        rm(self, "*.pdb", os.path.join(self.package_folder, "lib"))
        rm(self, "*.pdb", os.path.join(self.package_folder, "bin"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "SFCGAL")
        self.cpp_info.set_property("cmake_target_name", "SFCGAL")
        suffix = "d" if self.settings.build_type == "Debug" else ""
        self.cpp_info.libs = ["SFCGAL" + suffix]
