from conan import ConanFile
from conan.tools.cmake import cmake_layout, CMake, CMakeDeps


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeToolchain"

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        self.tool_requires(self.tested_reference_str)

    def generate(self):
        deps = CMakeDeps(self)
        deps.build_context_activated.append("cmrc")
        deps.build_context_build_modules.append("cmrc")
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()

    def test(self):
        return
