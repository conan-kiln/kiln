import os

from conan import ConanFile
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.layout import basic_layout
from conan.tools.microsoft import unix_path_package_info_legacy

required_conan_version = ">=2.1"


class GtkDocStubConan(ConanFile):
    name = "gtk-doc-stub"
    homepage = "https://gitlab.gnome.org/GNOME/gtk-doc-stub"
    description = "Helper scripts for generating GTK documentation"
    url = "https://github.com/conan-io/conan-center-index"
    license = "GPL-2.0-or-later"
    topics = ("gtk", "documentation", "gtkdocize")
    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        basic_layout(self, src_folder="src")

    def build_requirements(self):
        if self.settings_build.os == "Windows":
            self.win_bash = True
            if not self.conf.get("tools.microsoft.bash:path", check_type=str):
                self.tool_requires("msys2/latest")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        virtual_build_env = VirtualBuildEnv(self)
        virtual_build_env.generate()
        tc = AutotoolsToolchain(self)
        tc.generate()

    def build(self):
        autotools = Autotools(self)
        autotools.configure()
        autotools.make()

    def package(self):
        copy(self, "COPYING", self.source_folder, os.path.join(self.package_folder, "licenses"))
        autotools = Autotools(self)
        autotools.install()

    def package_info(self):
        self.cpp_info.includedirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = ["share"]

        self.buildenv_info.append_path("PATH", os.path.join(self.package_folder, "bin"))

        automake_dir = unix_path_package_info_legacy(self, os.path.join(self.package_folder, "share", "aclocal"))
        self.buildenv_info.append_path("ACLOCAL_PATH", automake_dir)
