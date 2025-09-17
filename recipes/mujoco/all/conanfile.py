import os
import textwrap

from conan import ConanFile
from conan.tools.build import check_min_cppstd, check_min_cstd, stdcpp_library
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class MujocoConan(ConanFile):
    name = "mujoco"
    description = "MuJoCo: Multi-Joint dynamics with Contact. A general purpose physics simulator."
    license = "Apache-2.0"
    homepage = "https://mujoco.org"
    topics = ("physics", "simulation", "robotics", "contact", "dynamics")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "tools": [True, False],
        "avx": [True, False],
        "avx_intrinsics": [True, False],
        "with_openusd": [True, False],
    }
    default_options = {
        "shared": True,
        "tools": False,
        "avx": True,
        "avx_intrinsics": True,
        "with_openusd": False,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.arch != "x86_64":
            del self.options.avx
            del self.options.avx_intrinsics

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("eigen/3.4.0")
        self.requires("tinyxml2/[*]")
        self.requires("tinyobjloader/[^2, include_prerelease]")
        self.requires("libccd/[^2.1]", options={"double_precision": True})
        self.requires("qhull/[^8]")
        self.requires("lodepng/[*]")
        self.requires("marchingcubecpp/[*]")
        self.requires("trianglemeshdistance/[*]")
        if self.options.with_openusd:
            self.requires("openusd/[*]")
        if self.options.tools:
            self.requires("glfw/[^3]")

    def validate(self):
        check_min_cppstd(self, 17)
        if self.settings.get_safe("compiler.cstd"):
            check_min_cstd(self, 11)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.16]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        for f in [
            "cmake/MujocoOptions.cmake",
            "python/mujoco/CMakeLists.txt",
            "simulate/cmake/SimulateOptions.cmake",
        ]:
            replace_in_file(self, f, "-Werror", "")
        save(self, "cmake/MujocoDependencies.cmake", textwrap.dedent("""\
            find_package(lodepng REQUIRED)
            find_package(marchingcubecpp REQUIRED)
            find_package(Qhull REQUIRED)
            find_package(tinyxml2 REQUIRED)
            find_package(tinyobjloader REQUIRED)
            find_package(trianglemeshdistance REQUIRED)
            find_package(ccd REQUIRED)
            link_libraries(
              lodepng
              marchingcubecpp::marchingcubecpp
              Qhull::qhullstatic_r
              tinyxml2::tinyxml2
              tinyobjloader::tinyobjloader
              trianglemeshdistance::trianglemeshdistance
              ccd
            )
            if(MUJOCO_WITH_USD)
              find_package(pxr REQUIRED)
              link_libraries(${PXR_LIBRARIES})
            endif()
        """))
        save(self, "simulate/cmake/SimulateDependencies.cmake", textwrap.dedent("""\
            find_package(glfw3 REQUIRED)
            find_package(Threads REQUIRED)
        """))


    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["FETCHCONTENT_FULLY_DISCONNECTED"] = True
        tc.cache_variables["MUJOCO_BUILD_TESTS"] = False
        tc.cache_variables["MUJOCO_BUILD_EXAMPLES"] = False
        tc.cache_variables["BUILD_TESTING"] = False
        tc.cache_variables["MUJOCO_BUILD_SIMULATE"] = self.options.tools
        tc.cache_variables["MUJOCO_ENABLE_AVX"] = self.options.get_safe("avx", False)
        tc.cache_variables["MUJOCO_ENABLE_AVX_INTRINSICS"] = self.options.get_safe("avx_intrinsics", False)
        tc.cache_variables["MUJOCO_WITH_USD"] = self.options.with_openusd
        tc.cache_variables["MUJOCO_SIMULATE_USE_SYSTEM_GLFW"] = True
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("lodepng", "cmake_target_name", "lodepng")
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "mujoco")
        self.cpp_info.components["core"].set_property("cmake_target_name", "mujoco::mujoco")
        self.cpp_info.components["core"].libs = ["mujoco"]
        self.cpp_info.components["core"].resdirs = ["share"]
        if not self.options.shared:
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.components["core"].system_libs = ["m", "pthread", "dl"]
            if stdcpp_library(self):
                self.cpp_info.components["core"].system_libs.append(stdcpp_library(self))
        if self.options.get_safe("avx_intrinsics"):
            self.cpp_info.components["core"].defines.append("mjUSEPLATFORMSIMD")
        if self.options.with_openusd:
            self.cpp_info.components["core"].defines.append("mjUSEUSD")
        requirements = [
            "eigen::eigen",
            "tinyxml2::tinyxml2",
            "tinyobjloader::tinyobjloader",
            "libccd::libccd",
            "qhull::qhull",
            "lodepng::lodepng",
            "marchingcubecpp::marchingcubecpp",
            "trianglemeshdistance::trianglemeshdistance",
        ]
        self.cpp_info.components["core"].requires = requirements

        if self.options.with_openusd:
            self.cpp_info.components["usdMjcf"].set_property("cmake_target_name", "mujoco::usdMjcf")
            self.cpp_info.components["usdMjcf"].libs = ["usdMjcf"]
            self.cpp_info.components["usdMjcf"].libdirs = ["lib/mujocoUsd"]
            self.cpp_info.components["usdMjcf"].resdirs = ["lib/mujocoUsd/resources"]
            self.cpp_info.components["usdMjcf"].requires = requirements + ["openusd::openusd"]

            self.cpp_info.components["mjcPhysics"].set_property("cmake_target_name", "mujoco::mjcPhysics")
            self.cpp_info.components["mjcPhysics"].libs = ["mjcPhysics"]
            self.cpp_info.components["mjcPhysics"].libdirs = ["lib/mujocoUsd"]
            self.cpp_info.components["mjcPhysics"].resdirs = ["lib/mujocoUsd/resources"]
            self.cpp_info.components["mjcPhysics"].requires = requirements + ["openusd::openusd"]

        if self.options.tools:
            self.cpp_info.components["_simulate"].requires = ["glfw::glfw"]
