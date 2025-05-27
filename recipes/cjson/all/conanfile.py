import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration, ConanException
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc, is_msvc_static_runtime
from conan.tools.scm import Version

required_conan_version = ">=2.4"


class CjsonConan(ConanFile):
    name = "cjson"
    description = "Ultralightweight JSON parser in ANSI C."
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/DaveGamble/cJSON"
    topics = ("json", "parser")
    settings = "os", "arch", "compiler", "build_type"
    package_type = "library"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "utils": [True, False],
        "use_locales": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "utils": False,
        "use_locales": True,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        if self.options.shared and is_msvc(self) and is_msvc_static_runtime(self):
            raise ConanInvalidConfiguration("shared cjson is not supported with MT runtime")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["ENABLE_SANITIZERS"] = False
        tc.variables["ENABLE_SAFE_STACK"] = False
        tc.variables["ENABLE_PUBLIC_SYMBOLS"] = True
        tc.variables["ENABLE_HIDDEN_SYMBOLS"] = False
        tc.variables["ENABLE_TARGET_EXPORT"] = False
        tc.variables["BUILD_SHARED_AND_STATIC_LIBS"] = False
        tc.variables["CJSON_OVERRIDE_BUILD_SHARED_LIBS"] = False
        tc.variables["ENABLE_CJSON_UTILS"] = self.options.utils
        tc.variables["ENABLE_CJSON_TEST"] = False
        tc.variables["ENABLE_LOCALES"] = self.options.use_locales
        tc.variables["ENABLE_FUZZING"] = False
        tc.variables["ENABLE_CUSTOM_COMPILER_FLAGS"] = False
        # Relocatable shared lib on Macos
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0042"] = "NEW"
        tc.cache_variables["CMAKE_POLICY_VERSION_MINIMUM"] = "3.5" # CMake 4 support
        if Version(self.version) > "1.7.18":
            raise ConanException("CMAKE_POLICY_VERSION_MINIMUM hardcoded to 3.5, check if new version supports CMake 4")
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "cJSON")

        self.cpp_info.components["_cjson"].set_property("cmake_target_name", "cjson")
        self.cpp_info.components["_cjson"].set_property("pkg_config_name", "libcjson")
        self.cpp_info.components["_cjson"].libs = ["cjson"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["_cjson"].system_libs = ["m"]

        if self.options.utils:
            self.cpp_info.components["cjson_utils"].set_property("cmake_target_name", "cjson_utils")
            self.cpp_info.components["cjson_utils"].set_property("pkg_config_name", "libcjson_utils")
            self.cpp_info.components["cjson_utils"].libs = ["cjson_utils"]
            self.cpp_info.components["cjson_utils"].requires = ["_cjson"]
