import os
import shutil

from conan import ConanFile
from conan.tools.build import cross_building, can_run
from conan.tools.gnu import AutotoolsToolchain, Autotools
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc, unix_path

required_conan_version = ">=2.1"


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    exports_sources = "configure.ac", "Makefile.am", "test_package.c"
    win_bash = True # This assignment must be *here* to avoid "Cannot wrap command with different envs." in Conan 1.x

    def layout(self):
        basic_layout(self)

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)
        self.tool_requires("autoconf/[^2.71]")    # Needed for autoreconf
        self.tool_requires("automake/[^1.18.1]")  # Needed for aclocal called by autoreconf--does Coanan 2.0 need a transitive_run trait?
        if self.settings_build.os == "Windows":
            self.win_bash = True
            if not self.conf.get("tools.microsoft.bash:path", check_type=str):
                self.tool_requires("msys2/latest")

    def generate(self):
        tc = AutotoolsToolchain(self)
        env = tc.environment()
        if is_msvc(self):
            env.define("CC", "cl -nologo")
            env.define("CXX", "cl -nologo")
        tc.generate(env)

    def build(self):
        if not cross_building(self):
            for src in self.exports_sources:
                shutil.copy(os.path.join(self.source_folder, src), self.build_folder)
            self.run("autoreconf -fiv")
            autotools = Autotools(self)
            autotools.configure(build_script_folder=self.build_folder)
            autotools.make()

    def test(self):
        if can_run(self):
            self.run(unix_path(self, os.path.join(".", "test_package")))
