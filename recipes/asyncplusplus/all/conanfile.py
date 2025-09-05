import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc, check_min_vs
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class AsyncplusplusConan(ConanFile):
    name = "asyncplusplus"
    description = "Async++ concurrency framework for C++11"
    license = "MIT"
    homepage = "https://github.com/Amanieu/asyncplusplus"
    topics = ("async", "parallel", "task", "scheduler")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "Async++")
        self.cpp_info.set_property("cmake_target_name", "Async++")
        self.cpp_info.libs = ["async++"]
        if not self.options.shared:
            self.cpp_info.defines = ["LIBASYNC_STATIC"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["pthread"]

        if Version(self.version) >= "1.2" and is_msvc(self) and check_min_vs(self, 191):
            self.cpp_info.cxxflags.extend(["/Zc:__cplusplus"])
