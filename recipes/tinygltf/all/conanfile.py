import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd, valid_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class TinygltfConan(ConanFile):
    name = "tinygltf"
    description = "Header only C++11 tiny glTF 2.0 library."
    license = "MIT"
    homepage = "https://github.com/syoyo/tinygltf"
    topics = ("gltf", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "draco": [True, False],
        "json": ["nlohmann", "rapidjson"],
        "stb_image": [True, False],
        "stb_image_write": [True, False],
    }
    default_options = {
        "draco": False,
        "json": "nlohmann",
        "stb_image": True,
        "stb_image_write": True,
    }

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def requirements(self):
        if self.options.json == "nlohmann":
            self.requires("nlohmann_json/[^3]")
        elif self.options.json == "rapidjson":
            self.requires("rapidjson/[*]")
        if self.options.draco:
            self.requires("draco/[^1.5.6]")
        if self.options.stb_image or self.options.stb_image_write:
            self.requires("stb/[*]")

    def validate(self):
        check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        replace_in_file(self, "tiny_gltf.h", '#include "json.hpp"', "#include <nlohmann/json.hpp>")
        for include in ["document.h", "prettywriter.h", "rapidjson.h", "stringbuffer.h", "writer.h"]:
            replace_in_file(self, "tiny_gltf.h", f'#include "{include}"', f'#include <rapidjson/{include}>')

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        copy(self, "tiny_gltf.h", src=self.source_folder, dst=os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "TinyGLTF")
        self.cpp_info.set_property("cmake_target_name", "TinyGLTF::TinyGLTF")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        if self.options.draco:
            self.cpp_info.defines.append("TINYGLTF_ENABLE_DRACO")
        if self.options.json == "rapidjson":
            self.cpp_info.defines.append("TINYGLTF_USE_RAPIDJSON")
        if not self.options.stb_image:
            self.cpp_info.defines.append("TINYGLTF_NO_STB_IMAGE")
        if not self.options.stb_image_write:
            self.cpp_info.defines.append("TINYGLTF_NO_STB_IMAGE_WRITE")
        if valid_min_cppstd(self, 14):
            self.cpp_info.defines.append("TINYGLTF_USE_CPP14")
