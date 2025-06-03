import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class OpenTracingConan(ConanFile):
    name = "opentracing-cpp"
    description = "C++ implementation of the OpenTracing API http://opentracing.io"
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/opentracing/opentracing-cpp"
    topics = "opentracing"
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "enable_mocktracer": [True, False],
        "enable_dynamic_load": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "enable_mocktracer": False,
        "enable_dynamic_load": False,
    }
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        # CMake v4 support
        replace_in_file(self, "CMakeLists.txt",
                        "cmake_minimum_required(VERSION 3.1)",
                        "cmake_minimum_required(VERSION 3.5)")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_MOCKTRACER"] = self.options.enable_mocktracer
        tc.variables["BUILD_DYNAMIC_LOADING"] = self.options.enable_dynamic_load
        tc.variables["BUILD_SHARED_LIBS"] = self.options.shared
        tc.variables["BUILD_STATIC_LIBS"] = not self.options.shared
        tc.variables["BUILD_TESTING"] = False
        tc.variables["ENABLE_LINTING"] = False
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()

        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "OpenTracing")
        self.cpp_info.set_property("cmake_target_name", "OpenTracing::OpenTracing")

        target_suffix = "" if self.options.shared else "-static"
        lib_suffix = "" if self.options.shared or self.settings.os != "Windows" else "-static"

        # opentracing
        opentracing = self.cpp_info.components["opentracing"]
        opentracing.set_property("cmake_target_name", "OpenTracing::opentracing" + target_suffix)
        opentracing.libs = ["opentracing" + lib_suffix]
        if not self.options.shared:
            opentracing.defines.append("OPENTRACING_STATIC")
        if self.options.enable_dynamic_load and self.settings.os in ("Linux", "FreeBSD"):
            opentracing.system_libs.append("dl")

        # opentracing_mocktracer
        if self.options.enable_mocktracer:
            opentracing_mocktracer = self.cpp_info.components["opentracing_mocktracer"]
            opentracing_mocktracer.set_property("cmake_target_name", "OpenTracing::opentracing_mocktracer" + target_suffix)
            opentracing_mocktracer.libs = ["opentracing_mocktracer" + lib_suffix]
            opentracing_mocktracer.requires = ["opentracing"]
            if not self.options.shared:
                opentracing_mocktracer.defines.append("OPENTRACING_MOCK_TRACER_STATIC")
