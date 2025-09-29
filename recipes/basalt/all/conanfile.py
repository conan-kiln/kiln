import os
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class BasaltConan(ConanFile):
    name = "basalt"
    description = "Basalt: Visual-Inertial Mapping with Non-Linear Factor Recovery"
    license = "BSD-3-Clause"
    homepage = "https://cvg.cit.tum.de/research/vslam/basalt"
    topics = ("computer-vision", "slam", "vio", "visual-inertial-odometry", "mapping")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "tools": [True, False],
        "instantiations_double": [True, False],
        "instantiations_float": [True, False],
        "with_cholmod": [True, False],
        "with_realsense": [True, False],
    }
    default_options = {
        "tools": False,
        "instantiations_double": False,
        "instantiations_float": False,
        "with_cholmod": False,
        "with_realsense": False,
    }

    def export_sources(self):
        export_conandata_patches(self)
        copy(self, "conan_deps.cmake", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))

    def configure(self):
        if not self.options.tools:
            self.options.with_realsense.value = False
        self.options["opencv"].imgproc = True
        self.options["opencv"].calib3d = True
        self.options["opencv"].highgui = True

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("eigen/[>=3.3 <6]", transitive_headers=True)
        self.requires("sophus/[^1]", transitive_headers=True)
        self.requires("cereal/[^1.3]", transitive_headers=True)
        self.requires("onetbb/[*]", transitive_headers=True, transitive_libs=True)
        self.requires("fmt/[*]", transitive_headers=True, transitive_libs=True)
        self.requires("nlohmann_json/[^3]")
        self.requires("magic_enum/[>=0.8 <1]")
        self.requires("pangolin/[>=0.8 <1]", transitive_headers=True, transitive_libs=True)
        self.requires("opengv/[*]")
        self.requires("opencv/[^4]")
        if self.options.with_cholmod:
            self.requires("suitesparse-cholmod/[^5]", transitive_headers=True, transitive_libs=True)
        if self.options.tools:
            self.requires("cli11/[^2]")
            if self.options.with_realsense:
                self.requires("librealsense/[^2.50]")

    def validate(self):
        check_min_cppstd(self, 17)
        opencv_opt = self.dependencies["opencv"].options
        if not all([opencv_opt.imgproc, opencv_opt.calib3d, opencv_opt.highgui]):
            raise ConanInvalidConfiguration("imgproc, calib3d, and highgui OpenCV modules must be enabled")

    def source(self):
        get(self, **self.conan_data["sources"][self.version]["source"], strip_root=True)
        get(self, **self.conan_data["sources"][self.version]["headers"], strip_root=True, destination="thirdparty/basalt-headers")
        apply_conandata_patches(self)
        rmdir(self, "cmake_modules")
        for p in Path("thirdparty").iterdir():
            if p.is_dir() and p.name not in ["basalt-headers", "apriltag"]:
                rmdir(self, p)
        # Relax an Eigen versin check
        replace_in_file(self, "CMakeLists.txt", "Eigen3 3.4.0", "Eigen3")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["CMAKE_PROJECT_basalt_INCLUDE"] = "conan_deps.cmake"
        tc.cache_variables["BUILD_TESTING"] = False
        tc.cache_variables["BASALT_BUILD_TOOLS"] = self.options.tools
        tc.cache_variables["BASALT_INSTANTIATIONS_DOUBLE"] = self.options.instantiations_double
        tc.cache_variables["BASALT_INSTANTIATIONS_FLOAT"] = self.options.instantiations_float
        tc.cache_variables["BASALT_USE_CHOLMOD"] = self.options.with_cholmod
        tc.cache_variables["BASALT_USE_REALSENSE2"] = self.options.with_realsense
        tc.cache_variables["BASALT_BUILTIN_SOPHUS"] = False
        tc.cache_variables["BASALT_BUILTIN_CEREAL"] = False
        tc.cache_variables["CXX_MARCH"] = False
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("eigen", "cmake_find_mode", "both")
        deps.set_property("onetbb", "cmake_target_name", "TBB::tbb")
        deps.set_property("magic_enum", "cmake_target_name", "basalt::magic_enum")
        deps.set_property("opengv", "cmake_target_name", "opengv")
        deps.set_property("nlohmann_json", "cmake_target_name", "nlohmann::json")
        deps.set_property("fmt", "cmake_target_name", "fmt::fmt")
        deps.set_property("cli11", "cmake_target_name", "basalt::cli11")
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        copy(self, "*", os.path.join(self.source_folder, "thirdparty", "basalt-headers", "include"), os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.set_property("cmake_target_name", "basalt::basalt")
        self.cpp_info.libs = ["basalt"]
        self.cpp_info.resdirs = ["etc"]
        if self.options.with_cholmod:
            self.cpp_info.defines.append("BASALT_USE_CHOLMOD")
        # Recommended, but not adding to not inadvertently break other consuming code:
        # self.cpp_info.defines.append("EIGEN_DONT_PARALLELIZE")
