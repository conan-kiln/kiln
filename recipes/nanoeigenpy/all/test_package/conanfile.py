import os

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import cmake_layout, CMake, CMakeToolchain


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps"

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        self.requires(self.tested_reference_str)
        self.requires("cpython/[^3.12]")

    def build_requirements(self):
        self.tool_requires("cpython/<host_version>")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["Python_EXECUTABLE"] = os.path.join(self.dependencies.build["cpython"].package_folder, "bin", "python").replace("\\", "/")
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if can_run(self):
            self.run('python -c "import test_package"', env="conanrun", cwd=self.cpp.build.bindir)
