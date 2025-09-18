import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class CryptoPPConan(ConanFile):
    name = "cryptopp"
    homepage = "https://cryptopp.com"
    license = "BSL-1.0"
    description = "Crypto++ Library is a free C++ class library of cryptographic schemes."
    topics = ("crypto", "cryptographic", "security")
    package_type = "static-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "openmp": [True, False],
    }
    default_options = {
        "openmp": True,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.openmp:
            self.requires("openmp/system")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.20 <5]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version]["source"], strip_root=True)
        get(self, **self.conan_data["sources"][self.version]["cmake"], destination="cryptopp-cmake", strip_root=True)
        apply_conandata_patches(self)
        replace_in_file(self, "cryptopp-cmake/cryptopp/CMakeLists.txt", "set(CMAKE_POSITION_INDEPENDENT_CODE 1)", "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["CRYPTOPP_SOURCES"] = self.source_folder.replace("\\", "/")
        tc.cache_variables["CRYPTOPP_BUILD_TESTING"] = False
        tc.cache_variables["CRYPTOPP_BUILD_DOCUMENTATION"] = False
        tc.cache_variables["CRYPTOPP_USE_INTERMEDIATE_OBJECTS_TARGET"] = False
        if self.settings.os == "Android":
            tc.cache_variables["CRYPTOPP_NATIVE_ARCH"] = True
        tc.cache_variables["CRYPTOPP_USE_OPENMP"] = self.options.openmp
        tc.cache_variables["CMAKE_DISABLE_FIND_PACKAGE_Git"] = True
        tc.generate()

    def _ensure_android_cpufeatures(self):
        # Use cpu-features.h from Android NDK
        if self.settings.os == "Android" and Version(self.version) < "8.4.0":
            # Replicate logic from: https://github.com/weidai11/cryptopp/blob/CRYPTOPP_8_2_0/cpu.cpp#L46-L52
            # In more recent versions this is already taken care of by cryptopp-cmake
            android_ndk_home = self.conf.get("tools.android:ndk_path")
            if android_ndk_home:
                copy(self, "cpu-features.h", os.path.join(android_ndk_home, "sources", "android", "cpufeatures"), self.source_folder)

    def build(self):
        self._ensure_android_cpufeatures()
        cmake = CMake(self)
        cmake.configure(build_script_folder="cryptopp-cmake")
        cmake.build()

    def package(self):
        copy(self, "License.txt", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        if Version(self.version) < "8.7.0":
            rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        else:
            rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "cryptopp")
        self.cpp_info.set_property("cmake_target_name", "cryptopp::cryptopp")
        self.cpp_info.set_property("pkg_config_name", "libcryptopp")

        self.cpp_info.libs = collect_libs(self)
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["pthread", "m"]
        elif self.settings.os == "SunOS":
            self.cpp_info.system_libs = ["nsl", "socket"]
        elif self.settings.os == "Windows":
            self.cpp_info.system_libs = ["bcrypt", "ws2_32"]
