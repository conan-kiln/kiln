import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.cmake import CMake, CMakeToolchain, CMakeDeps, cmake_layout
from conan.tools.files import *
from conan.tools.gnu import PkgConfigDeps
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class Nghttp2Conan(ConanFile):
    name = "libnghttp2"
    description = "HTTP/2 C Library and tools"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://nghttp2.org"
    topics = ("http", "http2")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_app": [True, False],
        "with_hpack": [True, False],
        "with_jemalloc": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_app": False,
        "with_hpack": False,
        "with_jemalloc": False,
    }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if not (self.options.with_app or self.options.with_hpack):
            self.settings.rm_safe("compiler.cppstd")
            self.settings.rm_safe("compiler.libcxx")
        if not self.options.with_app:
            del self.options.with_jemalloc

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_app:
            self.requires("openssl/[>=1.1 <4]")
        if self.options.with_app:
            self.requires("c-ares/[^1.25.0]")
            self.requires("libev/[^4.33]")
            self.requires("libevent/[^2.1.12]")
            self.requires("libxml2/[^2.12.5]")
            self.requires("zlib-ng/[^2.0]")
            if self.options.with_jemalloc:
                self.requires("jemalloc/[^5.3.0]")
        if self.options.with_hpack:
            self.requires("jansson/[^2.14]")

    def validate(self):
        if self.settings.compiler == "gcc" and Version(self.settings.compiler.version) < "6":
            raise ConanInvalidConfiguration(f"{self.ref} requires GCC >= 6.0")

    def build_requirements(self):
        if not self.conf.get("tools.gnu:pkg_config", default=False, check_type=str):
            self.tool_requires("pkgconf/[>=2.2 <3]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        if Version(self.version) < "1.60.0":
            tc.variables["ENABLE_SHARED_LIB"] = self.options.shared
            tc.variables["ENABLE_STATIC_LIB"] = not self.options.shared
        else:
            tc.variables["BUILD_STATIC_LIBS"] = not self.options.shared
        tc.variables["ENABLE_HPACK_TOOLS"] = self.options.with_hpack
        tc.variables["ENABLE_APP"] = self.options.with_app
        tc.variables["ENABLE_EXAMPLES"] = False
        tc.variables["ENABLE_FAILMALLOC"] = False
        # disable unneeded auto-picked dependencies
        tc.variables["WITH_LIBXML2"] = False
        tc.variables["WITH_JEMALLOC"] = self.options.get_safe("with_jemalloc", False)
        # To avoid overwriting dll import lib by static lib
        if Version(self.version) >= "1.60.0" and self.options.shared:
            tc.variables["STATIC_LIB_SUFFIX"] = "-static"
        if is_apple_os(self):
            # workaround for: install TARGETS given no BUNDLE DESTINATION for MACOSX_BUNDLE executable
            tc.cache_variables["CMAKE_MACOSX_BUNDLE"] = False
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()
        tc = PkgConfigDeps(self)
        tc.generate()

    def _patch_sources(self):
        if not self.options.shared and Version(self.version) < "1.60.0":
            # easier to patch here rather than have patch 'nghttp_static_include_directories' for each version
            save(self, os.path.join(self.source_folder, "lib", "CMakeLists.txt"),
                       "target_include_directories(nghttp2_static INTERFACE\n"
                       "${CMAKE_CURRENT_BINARY_DIR}/includes\n"
                       "${CMAKE_CURRENT_SOURCE_DIR}/includes)\n",
                       append=True)
        target_libnghttp2 = "nghttp2" if self.options.shared else "nghttp2_static"
        replace_in_file(self, os.path.join(self.source_folder, "src", "CMakeLists.txt"),
                              "\n"
                              "link_libraries(\n"
                              "  nghttp2\n",
                              "\n"
                              "link_libraries(\n"
                              "  {} ${{CONAN_LIBS}}\n".format(target_libnghttp2))
        replace_in_file(self, os.path.join(self.source_folder, "CMakeLists.txt"), "add_subdirectory(examples)", "")
        replace_in_file(self, os.path.join(self.source_folder, "CMakeLists.txt"), "add_subdirectory(tests)", "")

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern="COPYING", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.components["nghttp2"].set_property("pkg_config_name", "libnghttp2")
        self.cpp_info.components["nghttp2"].libs = ["nghttp2"]
        if is_msvc(self) and not self.options.shared:
            self.cpp_info.components["nghttp2"].defines.append("NGHTTP2_STATICLIB")

        if self.options.with_app:
            self.cpp_info.components["nghttp2_app"].requires = [
                "openssl::openssl", "c-ares::c-ares", "libev::libev",
                "libevent::libevent", "libxml2::libxml2", "zlib-ng::zlib-ng",
            ]
            if self.options.with_jemalloc:
                self.cpp_info.components["nghttp2_app"].requires.append("jemalloc::jemalloc")

        if self.options.with_hpack:
            self.cpp_info.components["nghttp2_hpack"].requires = ["jansson::jansson"]

        # trick for internal conan usage to pick up in downsteam pc files the pc file including all libs components
        self.cpp_info.set_property("pkg_config_name", "libnghttp2")
