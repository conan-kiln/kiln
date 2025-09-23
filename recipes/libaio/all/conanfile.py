import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import cross_building
from conan.tools.env import VirtualRunEnv
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class LibaioConan(ConanFile):
    name = "libaio"
    description = "libaio provides the Linux-native API for async I/O."
    license = "LGPL-2.1-only"
    homepage = "https://pagure.io/libaio"
    topics = ("asynchronous", "aio", "async")
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

    @property
    def _user_info_build(self):
        return getattr(self, "user_info_build", self.deps_user_info)

    def layout(self):
        basic_layout(self, src_folder="src")

    def validate(self):
        if self.info.settings.os != "Linux":
            raise ConanInvalidConfiguration(f"{self.ref} is not supported on {self.info.settings.os}.")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], destination=self.source_folder, strip_root=True)

    def generate(self):
        if not cross_building(self):
            env = VirtualRunEnv(self)
            env.generate(scope="build")
        tc = AutotoolsToolchain(self)
        tc.generate()

    def build(self):
        autotools = Autotools(self)
        with chdir(self, self.source_folder):
            autotools.make(target="all")

    def package(self):
        copy(self, pattern="COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        autotools = Autotools(self)
        with chdir(self, self.source_folder):
            autotools.make(target="install", args=["prefix=" + self.package_folder])
        if self.options.shared:
            rm(self, "libaio.a", os.path.join(self.package_folder, "lib"))
        else:
            rm(self, "libaio.so*", os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.libs = ["aio"]
