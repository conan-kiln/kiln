import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout, CMakeDeps
from conan.tools.files import *

required_conan_version = ">=2.1"


class VulkanProfilesConan(ConanFile):
    name = "vulkan-profiles"
    description = "Vulkan Profiles Tools"
    license = "Apache-2.0"
    homepage = "https://github.com/KhronosGroup/Vulkan-Profiles"
    url = "https://github.com/conan-io/conan-center-index"
    topics = ("vulkan", "gpu")
    package_type = "shared-library"  # really header-library + application
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires(f"vulkan-headers/{self.version}", transitive_headers=True)
        self.requires(f"vulkan-utility-libraries/{self.version}")
        self.requires("valijson/[^1.0]")
        self.requires("jsoncpp/[^1.9.5]")

    def validate(self):
        check_min_cppstd(self, 17)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.22.0 <5]")
        # also requires Python 3.7+

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        replace_in_file(self, "CMakeLists.txt", "set(CMAKE_CXX_STANDARD ${PROFILES_CPP_STANDARD})", "")
        # Allow relocated share/vulkan/registry/profiles-0.8-latest.json to be found
        replace_in_file(self, "layer/profiles_json.cpp",
                        'const char *sdk_path = std::getenv("VULKAN_SDK");',
                        'const char *sdk_path = std::getenv("VULKAN_PROFILES_ROOT");')

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_TESTS"] = False
        tc.variables["VULKAN_HEADERS_INSTALL_DIR"] = self.dependencies["vulkan-headers"].package_folder.replace("\\", "/")
        tc.generate()
        deps = CMakeDeps(self)
        deps.set_property("jsoncpp", "cmake_target_name", "jsoncpp_static")
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE*", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        # No official CMake config or target is exported by the project.

        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = ["share"]
        # Look for dynamically-linked libraries here
        if self.settings.os != "Windows":
            self.cpp_info.bindirs = ["lib"]

        if self.settings.os == "Windows":
            manifest_dir = "bin"
        else:
            manifest_dir = os.path.join("share", "vulkan", "explicit_layer.d")
        self.runenv_info.append_path("VK_LAYER_PATH", os.path.join(self.package_folder, manifest_dir))

        self.runenv_info.define_path("VULKAN_PROFILES_ROOT", self.package_folder)

        three_part_version = self.version.rsplit(".", 1)[0]
        self.cpp_info.set_property("system_package_version", three_part_version)
