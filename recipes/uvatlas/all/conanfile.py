import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class UVAtlasConan(ConanFile):
    name = "uvatlas"
    description = "UVAtlas Isochart Atlas Library for creating and packing isochart texture atlases"
    license = "MIT"
    homepage = "https://github.com/Microsoft/UVAtlas"
    topics = ("uv-mapping", "texture-atlas", "3d-graphics", "mesh-processing", "directx")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_openmp": [True, False],
        "with_eigen": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_openmp": True,
        "with_eigen": True,
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("directxmath/[*]", transitive_headers=True, transitive_libs=True)
        self.requires("directx-headers/[^1]", transitive_headers=True, transitive_libs=True)
        if self.options.with_openmp:
            self.requires("openmp/system")
        if self.options.with_eigen:
            self.requires("eigen/[>=3.3 <6]")
            self.requires("spectra/[^1.0]")

    def validate(self):
        check_min_cppstd(self, 17)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.20]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_TESTING"] = False
        tc.cache_variables["BUILD_TOOLS"] = False
        tc.cache_variables["BUILD_SHARED_LIBS"] = self.options.shared
        tc.cache_variables["UVATLAS_USE_OPENMP"] = self.options.with_openmp
        tc.cache_variables["ENABLE_USE_EIGEN"] = self.options.with_eigen
        tc.cache_variables["CMAKE_REQUIRE_FIND_PACKAGE_directxmath"] = True
        tc.cache_variables["CMAKE_REQUIRE_FIND_PACKAGE_directx-headers"] = True
        tc.cache_variables["CMAKE_REQUIRE_FIND_PACKAGE_OpenMP"] = True
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
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "uvatlas")
        self.cpp_info.set_property("cmake_target_name", "Microsoft::UVAtlas")
        self.cpp_info.set_property("pkg_config_name", "UVAtlas")
        self.cpp_info.libs = ["UVAtlas"]
        self.cpp_info.defines.append("USING_DIRECTX_HEADERS")
        if self.settings.os == "Windows" and self.options.shared:
            self.cpp_info.defines.append("UVATLAS_IMPORT")
