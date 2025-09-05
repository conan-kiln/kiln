import os
import textwrap

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class BtyaccConan(ConanFile):
    name = "btyacc"
    homepage = "https://github.com/ChrisDodd/btyacc"
    description = "Backtracking yacc"
    topics = "yacc", "parser"
    license = "Unlicense"
    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "fPIC": [True, False],
    }
    default_options = {
        "fPIC": True,
    }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    @property
    def _cmake_variables(self):
        return os.path.join("bin", "cmake", f"conan-official-{self.name}-variables.cmake")

    def package(self):
        copy(self, "README*", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))
        content = textwrap.dedent("""\
            set(BTYACC_EXECUTABLE "${CMAKE_CURRENT_LIST_DIR}/../btyacc")
            if(NOT EXISTS "${BTYACC_EXECUTABLE}")
                set(BTYACC_EXECUTABLE "${BTYACC_EXECUTABLE}.exe")
            endif()
        """)
        save(self, os.path.join(self.package_folder, self._cmake_variables), content)

    def package_info(self):
        self.cpp_info.includedirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.set_property("cmake_build_modules", [self._cmake_variables])
