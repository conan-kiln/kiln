import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class RTTRConan(ConanFile):
    name = "rttr"
    description = "Run Time Type Reflection library"
    topics = ("reflection",)
    homepage = "https://github.com/rttrorg/rttr"
    license = "MIT"

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_rtti": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_rtti": False,
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

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_DOCUMENTATION"] = False
        tc.variables["BUILD_EXAMPLES"] = False
        tc.variables["BUILD_UNIT_TESTS"] = False
        tc.variables["BUILD_WITH_RTTI"] = self.options.with_rtti
        tc.variables["BUILD_PACKAGE"] = False
        tc.variables["BUILD_RTTR_DYNAMIC"] = self.options.shared
        tc.variables["BUILD_STATIC"] = not self.options.shared
        tc.generate()

    def _patch_sources(self):
        # No warnings as errors
        for target in ["rttr_core", "rttr_core_lib", "rttr_core_s", "rttr_core_lib_s"]:
            replace_in_file(
                self,
                os.path.join(self.source_folder, "src", "rttr", "CMakeLists.txt"),
                f"set_compiler_warnings({target})",
                "",
            )

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE.txt", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "cmake"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        rm(self, "*.pdb", os.path.join(self.package_folder, "bin"))

    def package_info(self):
        cmake_target = "Core" if self.options.shared else "Core_Lib"
        self.cpp_info.set_property("cmake_file_name", "rttr")
        self.cpp_info.set_property("cmake_target_name", f"RTTR::{cmake_target}")
        self.cpp_info.libs = collect_libs(self)
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["dl", "pthread"]
        if self.options.shared:
            self.cpp_info.defines = ["RTTR_DLL"]
