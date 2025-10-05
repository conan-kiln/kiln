import os
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd, cross_building
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc_static_runtime

required_conan_version = ">=2.1"


class CupochConan(ConanFile):
    name = "cupoch"
    description = "GPU-accelerated 3D data processing library for robotics using CUDA"
    license = "MIT"
    homepage = "https://github.com/neka-nat/cupoch"
    topics = ("3d", "robotics", "cuda", "gpu", "slam", "point-cloud")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_rmm": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_rmm": True,
        "flann/*:with_cuda": True,
    }
    implements = ["auto_shared_fpic"]

    python_requires = "conan-cuda/latest"
    python_requires_extend = "conan-cuda.Cuda"

    def export_sources(self):
        export_conandata_patches(self)
        copy(self, "conan_deps.cmake", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.cuda.requires("cudart", transitive_headers=True, transitive_libs=True)
        self.requires("dlpack/[>=0.8]", transitive_headers=True)
        self.requires("eigen/[>=3.3 <6]", transitive_headers=True)
        self.requires("flann/[^1.9]", transitive_headers=True, transitive_libs=True)
        self.requires("glew/[^2]", transitive_headers=True)
        self.requires("glfw/[^3]", transitive_headers=True)
        self.requires("imgui/[^1.80]")
        self.requires("jsoncpp/[^1.9.5]")
        self.requires("libjpeg-meta/latest")
        self.requires("liblzf/[^3.6]")
        self.requires("libpng/[~1.6]")
        self.requires("libsgm/[^3.1]", transitive_headers=True)
        self.requires("rply/[^1]")
        self.requires("spdlog/[^1]", transitive_headers=True, transitive_libs=True)
        self.requires("stdgpu/1.3.0-nvblox.20240211", transitive_headers=True, transitive_libs=True)
        self.requires("tinyobjloader/[^2, include_prerelease]")
        self.requires("urdfdom/[^4]", transitive_headers=True, transitive_libs=True)
        if self.options.with_rmm:
            self.requires("rmm/[*]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        check_min_cppstd(self, 17)
        if self.cuda.major >= 13:
            raise ConanInvalidConfiguration(f"{self.ref} does not support CUDA 13 or newer")
        if not self.dependencies["flann"].options.with_cuda:
            raise ConanInvalidConfiguration("-o flann/*:with_cuda=True is required")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.27]")
        self.cuda.tool_requires("nvcc")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        for path in Path("third_party").iterdir():
            if path.name not in ["lbvh", "lbvh_index", "tomasakeninemoeller"]:
                rmdir(self, path)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["CMAKE_PROJECT_cupoch_INCLUDE"] = "conan_deps.cmake"
        tc.cache_variables["BUILD_UNIT_TESTS"] = False
        tc.cache_variables["STATIC_WINDOWS_RUNTIME"] = is_msvc_static_runtime(self)
        tc.cache_variables["USE_RMM"] = self.options.with_rmm
        tc.cache_variables["BUILD_PYTHON_MODULE"] = False
        if self.settings.os == "Linux" and not cross_building(self):
            tc.cache_variables["CMAKE_CUDA_IMPLICIT_INCLUDE_DIRECTORIES"] = "/usr/include"
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()
        cuda_tc = self.cuda.CudaToolchain()
        cuda_tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        copy(self, "*.h",
             os.path.join(self.source_folder, "third_party", "tomasakeninemoeller"),
             os.path.join(self.package_folder, "include", "tomasakeninemoeller"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "cupoch")
        self.cpp_info.set_property("cmake_target_name", "cupoch::cupoch")

        self.cpp_info.components["utility"].set_property("cmake_target_name", "cupoch::utility")
        self.cpp_info.components["utility"].libs = ["cupoch_utility"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["utility"].system_libs = ["m"]
        self.cpp_info.components["utility"].requires = [
            "cudart::cudart_",
            "dlpack::dlpack",
            "eigen::eigen",
            "jsoncpp::jsoncpp",
            "spdlog::spdlog",
            "stdgpu::stdgpu",
        ]
        if self.options.with_rmm:
            self.cpp_info.components["utility"].requires.append("rmm::rmm")

        self.cpp_info.components["io"].set_property("cmake_target_name", "cupoch::io")
        self.cpp_info.components["io"].libs = ["cupoch_io"]
        self.cpp_info.components["io"].requires = [
            "geometry",
            "utility",
            "tinyobjloader::tinyobjloader",
            "rply::rply",
            "liblzf::liblzf",
            "libpng::libpng",
            "libjpeg-meta::libjpeg-meta",
            "jsoncpp::jsoncpp",
        ]

        self.cpp_info.components["camera"].set_property("cmake_target_name", "cupoch::camera")
        self.cpp_info.components["camera"].libs = ["cupoch_camera"]
        self.cpp_info.components["camera"].requires = ["utility"]

        self.cpp_info.components["collision"].set_property("cmake_target_name", "cupoch::collision")
        self.cpp_info.components["collision"].libs = ["cupoch_collision"]
        self.cpp_info.components["collision"].requires = ["geometry"]

        self.cpp_info.components["geometry"].set_property("cmake_target_name", "cupoch::geometry")
        self.cpp_info.components["geometry"].libs = ["cupoch_geometry"]
        self.cpp_info.components["geometry"].requires = ["utility", "camera", "knn"]

        self.cpp_info.components["integration"].set_property("cmake_target_name", "cupoch::integration")
        self.cpp_info.components["integration"].libs = ["cupoch_integration"]
        self.cpp_info.components["integration"].requires = ["camera", "geometry", "utility"]

        self.cpp_info.components["imageproc"].set_property("cmake_target_name", "cupoch::imageproc")
        self.cpp_info.components["imageproc"].libs = ["cupoch_imageproc"]
        self.cpp_info.components["imageproc"].requires = ["utility", "geometry", "libsgm::libsgm"]

        self.cpp_info.components["kinematics"].set_property("cmake_target_name", "cupoch::kinematics")
        self.cpp_info.components["kinematics"].libs = ["cupoch_kinematics"]
        self.cpp_info.components["kinematics"].requires = ["utility", "collision", "geometry", "io", "urdfdom::urdfdom"]

        self.cpp_info.components["kinfu"].set_property("cmake_target_name", "cupoch::kinfu")
        self.cpp_info.components["kinfu"].libs = ["cupoch_kinfu"]
        self.cpp_info.components["kinfu"].requires = ["camera", "geometry", "integration", "registration"]

        self.cpp_info.components["knn"].set_property("cmake_target_name", "cupoch::knn")
        self.cpp_info.components["knn"].libs = ["cupoch_knn"]
        self.cpp_info.components["knn"].requires = ["utility", "flann::flann_cuda"]

        self.cpp_info.components["odometry"].set_property("cmake_target_name", "cupoch::odometry")
        self.cpp_info.components["odometry"].libs = ["cupoch_odometry"]
        self.cpp_info.components["odometry"].requires = ["utility", "camera", "geometry", "registration"]

        self.cpp_info.components["planning"].set_property("cmake_target_name", "cupoch::planning")
        self.cpp_info.components["planning"].libs = ["cupoch_planning"]
        self.cpp_info.components["planning"].requires = ["utility", "geometry", "collision"]

        self.cpp_info.components["registration"].set_property("cmake_target_name", "cupoch::registration")
        self.cpp_info.components["registration"].libs = ["cupoch_registration"]
        self.cpp_info.components["registration"].requires = ["utility", "geometry", "knn"]

        self.cpp_info.components["visualization"].set_property("cmake_target_name", "cupoch::visualization")
        self.cpp_info.components["visualization"].libs = ["cupoch_visualization"]
        self.cpp_info.components["visualization"].requires = [
            "utility", "camera", "geometry", "io",
            "imgui::imgui", "glfw::glfw", "glew::glew",
        ]
