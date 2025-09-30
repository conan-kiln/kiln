import os

from conan import ConanFile
from conan.tools.apple import is_apple_os
from conan.tools.build import can_run
from conan.tools.cmake import cmake_layout, CMake, CMakeToolchain


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps"

    def requirements(self):
        self.requires(self.tested_reference_str)

    def layout(self):
        cmake_layout(self)

    @property
    def _backends(self):
        return [
            "allegro5",
            "android",
            "dx9",
            "dx10",
            "dx11",
            "dx12",
            "glfw",
            "glut",
            "metal",
            "opengl2",
            "opengl3",
            "osx",
            "sdl2",
            "sdlrenderer2",
            "sdlrenderer3",
            "vulkan",
            "win32",
            "wgpu",
        ]

    def generate(self):
        opts = self.dependencies[self.tested_reference_str].options
        tc = CMakeToolchain(self)
        if str(opts.get_safe("docking")) == "True":
            tc.preprocessor_definitions["DOCKING"] = None
        if str(opts.get_safe("enable_test_engine")) == "True":
            tc.preprocessor_definitions["ENABLE_TEST_ENGINE"] = None
        for backend in self._backends:
            if str(opts.get_safe(f"backend_{backend}", False)) == "True":
                tc.preprocessor_definitions[f"IMGUI_IMPL_{backend.upper()}"] = ""
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if can_run(self):
            bin_path = os.path.join(self.cpp.build.bindir, "test_package")
            self.run(bin_path, env="conanrun")

            if is_apple_os(self):
                bin_path = os.path.join(self.cpp.build.bindir, "test_package_objcxx")
                self.run(bin_path, env="conanrun")
