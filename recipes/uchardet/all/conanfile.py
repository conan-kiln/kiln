import os

from conan import ConanFile
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class UchardetConan(ConanFile):
    name = "uchardet"
    description = (
        "uchardet is an encoding detector library, which takes a "
        "sequence of bytes in an unknown character encoding and "
        "attempts to determine the encoding of the text. "
        "Returned encoding names are iconv-compatible."
    )
    license = "MPL-1.1"
    homepage = "https://github.com/freedesktop/uchardet"
    topics = ("encoding", "detector")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "check_sse2": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "check_sse2": True,
    }

    def config_options(self):
        if self.settings_build not in ("x86", "x86_64"):
            self.options.rm_safe("check_sse2")
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        if Version(self.version) < "0.0.8":
            # fix problem with macOS
            replace_in_file(self, "CMakeLists.txt",
                            "string(TOLOWER ${CMAKE_SYSTEM_PROCESSOR} TARGET_ARCHITECTURE)",
                            'string(TOLOWER "${CMAKE_SYSTEM_PROCESSOR}" TARGET_ARCHITECTURE)')
        # disable building of tests
        save(self, "doc/CMakeLists.txt", "")
        save(self, "test/CMakeLists.txt", "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CHECK_SSE2"] = self.options.get_safe("check_sse2", False)
        tc.variables["BUILD_BINARY"] = False
        tc.variables["BUILD_STATIC"] = not self.options.shared
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING",
             dst=os.path.join(self.package_folder, "licenses"),
             src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        fix_apple_shared_install_name(self)

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "libuchardet")
        self.cpp_info.libs = ["uchardet"]
        if self.options.shared:
            self.cpp_info.defines.append("UCHARDET_SHARED")
