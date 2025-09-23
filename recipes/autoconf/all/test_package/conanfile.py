import os

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.env import Environment
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    win_bash = True

    def layout(self):
        basic_layout(self)

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)
        self.tool_requires("m4/[^1.4.20]")
        if self.settings_build.os == "Windows" and not self.conf.get("tools.microsoft.bash:path", check_type=str):
            self.tool_requires("msys2/latest")

    def generate(self):
        tc = AutotoolsToolchain(self)
        tc.generate()
        if is_msvc(self):
            env = Environment()
            env.define("CC", "cl -nologo")
            env.define("CXX", "cl -nologo")
            env.vars(self).save_script("conanbuild_msvc")

    def build(self):
        for src in ("configure.ac", "config.h.in", "Makefile.in", "test_package_c.c", "test_package_cpp.cpp"):
            copy(self, src, self.source_folder, self.build_folder)
        self.run("autoconf --verbose")
        autotools = Autotools(self)
        autotools.configure(build_script_folder=self.build_folder)
        autotools.make()

    def test(self):
        self.win_bash = None
        if can_run(self):
            bin_path = os.path.join(self.build_folder, "test_package")
            self.run(bin_path, env="conanrun")
