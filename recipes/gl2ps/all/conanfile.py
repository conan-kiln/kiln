import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.4"


class Gl2psConan(ConanFile):
    name = "gl2ps"
    description = "GL2PS: an OpenGL to PostScript printing library"
    license = "GL2PS OR LGPL-2.0-or-later"
    homepage = "https://www.geuz.org/gl2ps/"
    topics = ("postscript", "opengl", "printing")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_png": [True, False],
        "with_zlib": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_png": True,
        "with_zlib": True,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("opengl/system", transitive_headers=True, transitive_libs=True)
        if self.options.with_png:
            self.requires("libpng/[~1.6]")
        if self.options.with_zlib:
            self.requires("zlib-ng/[^2.0]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["ENABLE_PNG"] = self.options.with_png
        tc.cache_variables["ENABLE_ZLIB"] = self.options.with_zlib
        # Only used for tests
        tc.cache_variables["CMAKE_DISABLE_FIND_PACKAGE_GLUT"] = True
        tc.cache_variables["CMAKE_DISABLE_FIND_PACKAGE_LATEX"] = True
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING.GL2PS", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "COPYING.LGPL", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.libs = ["gl2ps"]

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("m")

        if self.options.with_png:
            self.cpp_info.defines.append("GL2PS_HAVE_LIBPNG")
        if self.options.with_zlib:
            self.cpp_info.defines.append("GL2PS_HAVE_ZLIB")
        if self.settings.os == "Windows" and self.options.shared:
            self.cpp_info.defines.append("GL2PSDLL")
