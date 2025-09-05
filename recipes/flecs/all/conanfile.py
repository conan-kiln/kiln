import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.4"


class FlecsConan(ConanFile):
    name = "flecs"
    description = "A fast entity component system (ECS) for C & C++"
    license = "MIT"
    topics = ("gamedev", "cpp", "data-oriented-design", "c99",
              "game-development", "ecs", "entity-component-system",
              "cpp11", "ecs-framework")
    homepage = "https://github.com/SanderMertens/flecs"

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

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version],
            destination=self.source_folder, strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        if Version(self.version) < "3.0.1":
            tc.variables["FLECS_STATIC_LIBS"] = not self.options.shared
            tc.variables["FLECS_SHARED_LIBS"] = self.options.shared
            tc.variables["FLECS_DEVELOPER_WARNINGS"] = False
        else:
            tc.variables["FLECS_STATIC"] = not self.options.shared
            tc.variables["FLECS_SHARED"] = self.options.shared
            tc.variables["FLECS_TESTS"] = False
        tc.variables["FLECS_PIC"] = self.options.get_safe("fPIC", True)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        suffix = "" if self.options.shared else "_static"
        self.cpp_info.set_property("cmake_file_name", "flecs")
        self.cpp_info.set_property("cmake_target_name", f"flecs::flecs{suffix}")

        self.cpp_info.libs = [f"flecs{suffix}"]
        if not self.options.shared:
            self.cpp_info.defines.append("flecs_STATIC")
        if Version(self.version) >= "3.0.0":
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.system_libs.append("pthread")
            elif self.settings.os == "Windows":
                self.cpp_info.system_libs.extend(["wsock32", "ws2_32"])
