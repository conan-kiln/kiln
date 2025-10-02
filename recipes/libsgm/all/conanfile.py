import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class LibSGMConan(ConanFile):
    name = "libsgm"
    description = "Stereo Semi-Global Matching with CUDA"
    license = "Apache-2.0"
    homepage = "https://github.com/fixstars/libSGM"
    topics = ("stereo", "depth", "sgm", "cuda")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_opencv": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_opencv": False,
    }
    implements = ["auto_shared_fpic"]

    python_requires = "conan-cuda/latest"
    python_requires_extend = "conan-cuda.Cuda"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.cuda.requires("cudart")
        if self.options.with_opencv:
            self.requires("opencv/[^4]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        check_min_cppstd(self, 17)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.18]")
        self.cuda.tool_requires("nvcc")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # Avoid overlinking
        replace_in_file(self, "src/CMakeLists.txt", "${OpenCV_LIBS}", "opencv_core")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["LIBSGM_SHARED"] = self.options.shared
        tc.cache_variables["BUILD_OPENCV_WRAPPER"] = self.options.with_opencv
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()
        tc = self.cuda.CudaToolchain()
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("cmake_find_mode", "both")
        self.cpp_info.set_property("cmake_file_name", "LibSGM")
        self.cpp_info.set_property("cmake_additional_variables_prefixes", ["LIBSGM"])
        self.cpp_info.libs = ["sgm"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]
        self.cpp_info.requires = ["cudart::cudart_"]
        if self.options.with_opencv:
            self.cpp_info.requires.append("opencv::opencv_core")
