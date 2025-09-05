import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc, is_msvc_static_runtime

required_conan_version = ">=2.1"


class EffceeConan(ConanFile):
    name = "effcee"
    homepage = "https://github.com/google/effcee/"
    description = "Effcee is a C++ library for stateful pattern matching" \
                  " of strings, inspired by LLVM's FileCheck"
    topics = ("strings", "algorithm", "matcher")
    license = "Apache-2.0"
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

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("re2/[>=20220601]", transitive_headers=True)

    def validate(self):
        check_min_cppstd(self, 11)
        if self.options.shared and is_msvc(self) and is_msvc_static_runtime(self):
            raise ConanInvalidConfiguration(f"{self.ref} shared with MT runtime not supported by msvc")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        # CMake v4 support
        replace_in_file(self, "CMakeLists.txt",
                        "cmake_minimum_required(VERSION 3.1)",
                        "cmake_minimum_required(VERSION 3.5)")
        # Respect cppstd from Conan
        replace_in_file(self, "CMakeLists.txt", "set(CMAKE_CXX_STANDARD 11)", "")
        replace_in_file(self, "cmake/utils.cmake", "-std=c++11", "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["EFFCEE_BUILD_TESTING"] = False
        tc.variables["EFFCEE_BUILD_SAMPLES"] = False
        if self.settings.os == "Windows":
            if is_msvc(self):
                tc.variables["EFFCEE_ENABLE_SHARED_CRT"] = not is_msvc_static_runtime(self)
            else:
                # Do not force linkage to static libgcc and libstdc++ for MinGW
                tc.variables["EFFCEE_ENABLE_SHARED_CRT"] = True
        tc.variables["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = True
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["effcee"]
