import os

from conan import ConanFile
from conan.tools.cmake import CMakeToolchain, CMakeDeps, CMake
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class SwigMatlabConan(ConanFile):
    name = "swig-matlab"
    description = "A fork of SWIG with add MATLAB support"
    license = "GPL-3.0-or-later"
    homepage = "https://github.com/jaeandersson/swig/tree/matlab-customdoc"
    topics = ("matlab", "wrapper")
    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler

    def requirements(self):
        self.requires("pcre/[*]")

    def build_requirements(self):
        self.tool_requires("bison/[^3.8.2]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version]["swig"], strip_root=True)
        download(self, **self.conan_data["sources"][self.version]["cmakelists"], filename="CMakeLists.txt")
        download(self, **self.conan_data["sources"][self.version]["swigconfig"], filename="Tools/cmake/swigconfig.h.in")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()
        deps = CMakeDeps(self)
        deps.set_property("pcre", "cmake_file_name", "PCRE2")
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE*", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        copy(self, "COPYRIGHT", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        save(self, os.path.join(self.package_folder, "share/swig/conan-swig-variables.cmake"),
             "find_program(SWIG_EXECUTABLE swig)\n"
             'get_filename_component(SWIG_DIR "$ENV{SWIG_LIB}" ABSOLUTE)\n')

    def package_info(self):
        self.cpp_info.set_property("cmake_find_mode", "both")
        self.cpp_info.set_property("cmake_file_name", "SWIG")
        self.cpp_info.set_property("cmake_target_name", "SWIG::SWIG")
        self.cpp_info.includedirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.builddirs = ["share/swig"]
        self.cpp_info.set_property("cmake_build_modules", ["share/swig/conan-swig-variables.cmake"])

        version_str = self.version.split("+")[0]
        self.buildenv_info.define_path("SWIG_LIB", os.path.join(self.package_folder, "share", "swig", version_str))
