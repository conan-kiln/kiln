import os
from pathlib import Path

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.4"


class CgltfConan(ConanFile):
    name = "cgltf"
    description = "Single-file glTF 2.0 loader and writer written in C99."
    license = "MIT"
    homepage = "https://github.com/jkuhlmann/cgltf"
    topics = ("gltf",)
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
    languages = ["C"]

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        save(self, "cgltf.c", (
            '#define CGLTF_IMPLEMENTATION\n'
            '#include "cgltf.h"\n'
        ))
        save(self, "cgltf_write.c", (
            '#define CGLTF_WRITE_IMPLEMENTATION\n'
            '#include "cgltf_write.h"\n'
        ))

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def _remove_implementation(self, header_fullpath):
        header_content = load(self, header_fullpath)
        begin = header_content.find("/*\n *\n * Stop now, if you are only interested in the API.")
        end = header_content.find("/* cgltf is distributed under MIT license:", begin)
        implementation = header_content[begin:end]
        replace_in_file(self, header_fullpath, implementation,
                        "/**\n * Implementation removed by conan during packaging.\n * Don't forget to link libs provided in this package.\n */\n\n",)

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        for header_file in ["cgltf.h", "cgltf_write.h"]:
            header_fullpath = os.path.join(self.package_folder, "include", header_file)
            self._remove_implementation(header_fullpath)
        for dll in Path(self.package_folder, "lib").glob("*.dll"):
            rename(self, dll, Path(self.package_folder, "bin", dll.name))

    def package_info(self):
        self.cpp_info.libs = ["cgltf"]
