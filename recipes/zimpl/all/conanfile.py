import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc

required_conan_version = ">=2.1"


class ZimplConan(ConanFile):
    name = "zimpl"
    description = "ZIMPL is a language to translate the mathematical model of a problem into a LP or MIP program"
    license = "LGPL-3.0-or-later"
    homepage = "https://github.com/scipopt/zimpl"
    topics = ("optimization", "linear-programming", "mixed-integer-programming", "modeling-language")
    package_type = "static-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "fPIC": [True, False],
        "tools": [True, False],
    }
    default_options = {
        "fPIC": True,
        "tools": False,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("zlib-ng/[^2]")
        self.requires("gmp/[^6.3.0]")
        if is_msvc(self):
            self.requires("pcre/[^8]")

    def build_requirements(self):
        if self.settings.os == "Windows":
            self.tool_requires("winflexbison/[^2.5.25]")
        else:
            self.tool_requires("flex/[^2.6.4]")
            self.tool_requires("bison/[^3.8.2]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # Add missing source files to the library
        replace_in_file(self, "src/CMakeLists.txt",
                        "set(libsources",
                        "set(libsources "
                        "zimpl/xlpglue.c "
                        "zimpl/ratlpstore.c "
                        "zimpl/ratlpfwrite.c "
                        "zimpl/ratqbowrite.c "
                        "zimpl/ratmpswrite.c ")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()
        deps = CMakeDeps(self)
        deps.set_property("gmp", "cmake_file_name", "GMP")
        deps.set_property("pcre", "cmake_file_name", "PCRE")
        deps.generate()

    def _patch_sources(self):
        cmakelists = os.path.join(self.source_folder, "src", "CMakeLists.txt")
        if self.options.get_safe("fPIC", True):
            replace_in_file(self, cmakelists,
                            "install(TARGETS libzimpl zimpl libzimpl-pic",
                            "install(TARGETS zimpl libzimpl-pic")
            save(self, cmakelists, "\nset_target_properties(libzimpl PROPERTIES EXCLUDE_FROM_ALL 1)\n", append=True)
        else:
            replace_in_file(self, cmakelists,
                            "install(TARGETS libzimpl zimpl libzimpl-pic",
                            "install(TARGETS zimpl libzimpl")
            save(self, cmakelists, "\nset_target_properties(libzimpl-pic PROPERTIES EXCLUDE_FROM_ALL 1)\n", append=True)
        if not self.options.tools:
            replace_in_file(self, cmakelists, "install(TARGETS zimpl ", "install(TARGETS ")
            save(self, cmakelists, "\nset_target_properties(zimpl PROPERTIES EXCLUDE_FROM_ALL 1)\n", append=True)

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "zimpl")
        self.cpp_info.set_property("cmake_additional_variables_prefixes", ["ZIMPL"])
        self.cpp_info.set_property("cmake_target_aliases", ["libzimpl", "libzimpl-pic"])
        self.cpp_info.libs = ["zimpl-pic" if self.options.get_safe("fPIC", True) else "zimpl"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]
