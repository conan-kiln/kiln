import os

from conan import ConanFile
from conan.tools.build import cross_building
from conan.tools.env import Environment, VirtualRunEnv
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc, unix_path

required_conan_version = ">=2.1"


class DartsCloneConan(ConanFile):
    name = "darts-clone"
    description = "A clone of Darts (Double-ARray Trie System)"
    license = "BSD-2-Clause"
    homepage = "https://github.com/s-yata/darts-clone"
    topics = ("trie", "double-array-trie", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "tools": [True, False],
    }
    default_options = {
        "tools": False,
    }

    def package_id(self):
        if self.info.options.tools:
            del self.info.settings.compiler
        else:
            self.info.clear()

    def layout(self):
        basic_layout(self, src_folder="src")

    def build_requirements(self):
        if self.options.tools:
            self.tool_requires("libtool/[^2.4.7]")
            if self.settings_build.os == "Windows":
                self.win_bash = True
                if not self.conf.get("tools.microsoft.bash:path", check_type=str):
                    self.tool_requires("msys2/latest")
                if is_msvc(self):
                    self.tool_requires("automake/[^1.18.1]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        if not self.options.tools:
            return

        if not cross_building(self):
            VirtualRunEnv(self).generate(scope="build")

        tc = AutotoolsToolchain(self)
        tc.generate()

        if is_msvc(self):
            env = Environment()
            compile_wrapper = unix_path(self, self.conf.get("user.automake:compile-wrapper"))
            ar_wrapper = unix_path(self, self.conf.get("user.automake:lib-wrapper"))
            env.define("CC", f"{compile_wrapper} cl -nologo")
            env.define("CXX", f"{compile_wrapper} cl -nologo")
            env.define("LD", "link -nologo")
            env.define("AR", f"{ar_wrapper} lib")
            env.define("NM", "dumpbin -symbols")
            env.vars(self).save_script("conanbuild_msvc")

    def build(self):
        if self.options.tools:
            autotools = Autotools(self)
            autotools.autoreconf()
            autotools.configure()
            autotools.make()

    def package(self):
        copy(self, "COPYING*", self.source_folder, os.path.join(self.package_folder, "licenses"))
        if self.options.tools:
            autotools = Autotools(self)
            autotools.install()
        else:
            copy(self, "*.h", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))

    def package_info(self):
        # Unofficial names
        self.cpp_info.set_property("cmake_file_name", "darts")
        self.cpp_info.set_property("cmake_target_name", "darts::darts")
        self.cpp_info.set_property("pkg_config_name", "darts")

        self.cpp_info.libdirs = []
        self.cpp_info.bindirs = ["bin"] if self.options.tools else []
        self.cpp_info.includedirs = ["include"]
