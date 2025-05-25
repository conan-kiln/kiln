import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import stdcpp_library
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class SpirvCrossConan(ConanFile):
    name = "spirv-cross"
    description = "SPIRV-Cross is a practical tool and library for performing " \
                  "reflection on SPIR-V and disassembling SPIR-V back to high level languages."
    license = "Apache-2.0"
    topics = ("reflection", "disassembler", "spirv", "spir-v", "glsl", "hlsl")
    homepage = "https://github.com/KhronosGroup/SPIRV-Cross"
    url = "https://github.com/conan-io/conan-center-index"

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "c_api": [True, False],
        "build_executable": [True, False],
        "exceptions": [True, False],
        "glsl": [True, False],
        "hlsl": [True, False],
        "msl": [True, False],
        "cpp": [True, False],
        "reflect": [True, False],
        "util": [True, False],
        "namespace": ["ANY"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "c_api": False,
        "build_executable": True,
        "exceptions": True,
        "glsl": True,
        "hlsl": True,
        "msl": True,
        "cpp": True,
        "reflect": True,
        "util": True,
        "namespace": "spirv_cross",
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if not self.options.c_api:
            # The C++ part of the library is static-only
            self.options.rm_safe("shared")
            self.options.rm_safe("fPIC")
            self.package_type = "static-library"
        if self.options.get_safe("shared"):
            del self.options.util

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        if not self.options.glsl and \
           (self.options.hlsl or self.options.msl or self.options.cpp or self.options.reflect):
            raise ConanInvalidConfiguration("hlsl, msl, cpp and reflect require glsl enabled")

        if self.options.build_executable and \
           not (self.options.glsl and self.options.hlsl and self.options.msl and
                self.options.cpp and self.options.reflect and self.options.get_safe("util", True)):
            raise ConanInvalidConfiguration("executable can't be built without glsl, hlsl, msl, cpp, reflect and util")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["SPIRV_CROSS_EXCEPTIONS_TO_ASSERTIONS"] = not self.options.exceptions
        tc.variables["SPIRV_CROSS_SHARED"] = self.options.get_safe("shared", False)
        tc.variables["SPIRV_CROSS_STATIC"] = not self.options.get_safe("shared", False) or self.options.build_executable
        tc.variables["SPIRV_CROSS_CLI"] = self.options.build_executable
        tc.variables["SPIRV_CROSS_ENABLE_TESTS"] = False
        tc.variables["SPIRV_CROSS_ENABLE_GLSL"] = self.options.glsl
        tc.variables["SPIRV_CROSS_ENABLE_HLSL"] = self.options.hlsl
        tc.variables["SPIRV_CROSS_ENABLE_MSL"] = self.options.msl
        tc.variables["SPIRV_CROSS_ENABLE_CPP"] = self.options.cpp
        tc.variables["SPIRV_CROSS_ENABLE_REFLECT"] = self.options.reflect
        tc.variables["SPIRV_CROSS_ENABLE_C_API"] = self.options.c_api
        tc.variables["SPIRV_CROSS_ENABLE_UTIL"] = self.options.get_safe("util", False) or self.options.build_executable
        tc.variables["SPIRV_CROSS_SKIP_INSTALL"] = False
        tc.variables["SPIRV_CROSS_FORCE_PIC"] = self.options.get_safe("fPIC", True)
        tc.variables["SPIRV_CROSS_NAMESPACE_OVERRIDE"] = self.options.namespace
        if Version(self.version) < "1.3.280":
            tc.cache_variables["CMAKE_POLICY_VERSION_MINIMUM"] = "3.15" # CMake 4 support
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        rm(self, "*.ilk", os.path.join(self.package_folder, "bin"))
        rm(self, "*.pdb", os.path.join(self.package_folder, "bin"))
        if self.options.get_safe("shared") and self.options.build_executable:
            for static_lib in [
                "spirv-cross-core", "spirv-cross-glsl", "spirv-cross-hlsl", "spirv-cross-msl",
                "spirv-cross-cpp", "spirv-cross-reflect", "spirv-cross-c", "spirv-cross-util",
            ]:
                rm(self, f"*{static_lib}.*", os.path.join(self.package_folder, "lib"))

    def package_info(self):
        # FIXME: we should provide one CMake config file per target (waiting for an implementation of https://github.com/conan-io/conan/issues/9000)
        def _add_component(target_lib, requires=None, c_api_requires=False):
            component = self.cpp_info.components[target_lib]
            component.set_property("cmake_target_name", target_lib)
            if target_lib == "spirv-cross-c-shared":
                component.set_property("cmake_target_aliases", ["spirv-cross-c"])
                component.set_property("pkg_config_name", target_lib)
            prefix = "d" if self.settings.os == "Windows" and self.settings.build_type == "Debug" else ""
            component.libs = [f"{target_lib}{prefix}"]
            component.includedirs.append(os.path.join("include", "spirv_cross"))
            component.defines.append(f"SPIRV_CROSS_NAMESPACE_OVERRIDE={self.options.namespace}")
            component.requires.extend(requires or [])
            if self.settings.os in ["Linux", "FreeBSD"] and self.options.glsl:
                component.system_libs.append("m")
            if self.options.c_api:
                if not self.options.shared and stdcpp_library(self):
                    component.system_libs.append(stdcpp_library(self))
                if c_api_requires:
                    self.cpp_info.components["spirv-cross-c"].requires.append(target_lib)

        if self.options.get_safe("shared"):
            _add_component("spirv-cross-c-shared")
        else:
            _add_component("spirv-cross-core")
            if self.options.c_api:
                _add_component("spirv-cross-c")
            if self.options.glsl:
                _add_component("spirv-cross-glsl", requires=["spirv-cross-core"], c_api_requires=True)
                if self.options.hlsl:
                    _add_component("spirv-cross-hlsl", requires=["spirv-cross-glsl"], c_api_requires=True)
                if self.options.msl:
                    _add_component("spirv-cross-msl", requires=["spirv-cross-glsl"], c_api_requires=True)
                if self.options.cpp:
                    _add_component("spirv-cross-cpp", requires=["spirv-cross-glsl"], c_api_requires=True)
                if self.options.reflect:
                    _add_component("spirv-cross-reflect", c_api_requires=True)
            if self.options.util:
                _add_component("spirv-cross-util", requires=["spirv-cross-core"])
