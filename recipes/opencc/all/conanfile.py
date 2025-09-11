import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd, stdcpp_library
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class OpenCCConan(ConanFile):
    name = "opencc"
    description = ("Open Chinese Convert (OpenCC) is an open-source project for "
                   "conversions between Traditional Chinese, Simplified Chinese and Japanese Kanji (Shinjitai).")
    license = "Apache-2.0"
    homepage = "https://github.com/BYVoid/OpenCC"
    topics = ("simplified-chinese", "traditional-chinese", "kanji", "i18n")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "tools": [True, False],
        "with_darts": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "tools": False,
        "with_darts": True,
    }
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        copy(self, "conan_deps.cmake", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("marisa/[>=0.2 <1]", transitive_headers=True)
        self.requires("rapidjson/[*]", transitive_headers=True)
        self.requires("tclap/[^1.2]", transitive_headers=True)
        if self.options.with_darts:
            self.requires("darts-clone/[*]", transitive_headers=True)

    def validate(self):
        check_min_cppstd(self, 14)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        rmdir(self, "deps")
        replace_in_file(self, "CMakeLists.txt", "set(CMAKE_CXX_STANDARD 14)", "")
        replace_in_file(self, "CMakeLists.txt", "-std=c++14", "")
        replace_in_file(self, "CMakeLists.txt",
                        "find_library(LIBMARISA NAMES marisa)",
                        "find_package(Marisa REQUIRED)")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["CMAKE_PROJECT_opencc_INCLUDE"] = "conan_deps.cmake"
        tc.cache_variables["BUILD_DOCUMENTATION"] = False
        tc.cache_variables["ENABLE_GTEST"] = False
        tc.cache_variables["ENABLE_BENCHMARK"] = False
        tc.cache_variables["BUILD_PYTHON"] = False
        tc.cache_variables["ENABLE_DARTS"] = self.options.with_darts
        tc.cache_variables["USE_SYSTEM_MARISA"] = True
        tc.cache_variables["USE_SYSTEM_RAPIDJSON"] = True
        tc.cache_variables["USE_SYSTEM_TCLAP"] = True
        tc.cache_variables["USE_SYSTEM_DARTS"] = True
        tc.cache_variables["USE_SYSTEM_PYBIND11"] = False
        tc.cache_variables["DIR_SHARE_OPENCC"] = os.path.join(self.package_folder, "share", "opencc")
        tc.cache_variables["LIBMARISA"] = True
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("marisa", "cmake_target_name", "marisa")
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE*", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        if not self.options.tools:
            rmdir(self, os.path.join(self.package_folder, "bin"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "OpenCC")
        self.cpp_info.set_property("cmake_target_name", "OpenCC::OpenCC")
        self.cpp_info.set_property("pkg_config_name", "opencc")
        self.cpp_info.libs = ["opencc"]
        self.cpp_info.includedirs.append("include/opencc")
        self.cpp_info.resdirs = ["share/openacc"]
        if not self.options.shared:
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.system_libs = ["m", "dl"]
            if stdcpp_library(self):
                self.cpp_info.system_libs.append(stdcpp_library(self))
        self.cpp_info.requires = [
            "marisa::marisa",
            "rapidjson::rapidjson",
            "tclap::tclap",
        ]
        if self.options.with_darts:
            self.cpp_info.requires.append("darts-clone::darts-clone")
