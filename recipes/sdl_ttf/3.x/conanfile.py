import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.4"


class SdlTtfConan(ConanFile):
    name = "sdl_ttf"
    description = "A TrueType font library for SDL"
    license = "Zlib"
    homepage = "https://github.com/libsdl-org/SDL_ttf"
    topics = ("sdl3", "sdl3_ttf", "sdl", "ttf", "font")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_harfbuzz": [True, False],
        "with_plutosvg": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_harfbuzz": True,
        "with_plutosvg": True,
    }
    implements = ["auto_shared_fpic"]
    languages = "C"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("freetype/[^2.13.2]")
        self.requires("sdl/[^3.2.6]", transitive_headers=True)
        if self.options.with_harfbuzz:
            self.requires("harfbuzz/[>=8.3.0]")
        if self.options.with_plutosvg:
            self.requires("plutosvg/[>=0.0.7 <1]")

    def validate(self):
        if Version(self.version).major != self.dependencies["sdl"].ref.version.major:
            raise ConanInvalidConfiguration("sdl and sdl_ttf must have the same major version")
        if self.options.shared != self.dependencies["sdl"].options.shared:
            raise ConanInvalidConfiguration("sdl and sdl_ttf must be built with the same 'shared' option value")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.17]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["SDLTTF_VENDORED"] = False
        tc.cache_variables["SDLTTF_STRICT"] = True
        tc.cache_variables["SDLTTF_SAMPLES"] = False
        tc.cache_variables["SDLTTF_HARFBUZZ"] = self.options.with_harfbuzz
        tc.cache_variables["SDLTTF_PLUTOSVG"] = self.options.with_plutosvg
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "LICENSE.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "SDL3_ttf")
        self.cpp_info.set_property("cmake_target_name", "SDL3_ttf::SDL3_ttf")
        self.cpp_info.set_property("cmake_target_aliases", ["SDL3_ttf::SDL3_ttf-static"])
        self.cpp_info.set_property("pkg_config_name", "sdl3-ttf")
        lib_suffix = "-static" if self.settings.os == "Windows" and not self.options.shared else ""
        self.cpp_info.libs = [f"SDL3_ttf{lib_suffix}"]
