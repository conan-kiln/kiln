import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class NuRaftConan(ConanFile):
    name = "nuraft"
    homepage = "https://github.com/eBay/NuRaft"
    description = """Cornerstone based RAFT library."""
    topics = ("raft",)
    url = "https://github.com/conan-io/conan-center-index"
    license = "Apache-2.0"

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "asio": ["boost", "standalone"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "asio": "boost",
    }
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("openssl/[>=1.1 <4]")
        if self.options.asio == "boost":
            self.requires("boost/[^1.71.0 <1.88]", libs=False)
        else:
            self.requires("asio/[^1.27.0]", libs=False)

    def validate(self):
        if self.settings.os == "Windows":
            raise ConanInvalidConfiguration(f"{self.ref} doesn't support Windows")
        if self.settings.os == "Macos" and self.options.shared:
            raise ConanInvalidConfiguration(f"{self.ref} shared not supported for Macos")
        check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        if self.options.asio != "boost":
            tc.cache_variables["CMAKE_DISABLE_FIND_PACKAGE_Boost"] = True
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["nuraft"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.extend(["m", "pthread"])
