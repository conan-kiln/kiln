import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class I2cConan(ConanFile):
    name = "i2c-tools"
    description = "I2C tools for the linux kernel as well as an I2C library."
    license = "GPL-2.0-or-later AND LGPL-2.1-or-later"
    homepage = "https://i2c.wiki.kernel.org/index.php/I2C_Tools"
    topics = ("i2c",)
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
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("linux-headers-generic/[^6.5]")

    def validate(self):
        if self.settings.os not in ["Linux", "FreeBSD"]:
            raise ConanInvalidConfiguration("i2c-tools only support Linux")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        replace_in_file(self, "Makefile",
                        "SRCDIRS	:= include lib eeprom stub tools $(EXTRA)",
                        "SRCDIRS	:= include lib $(EXTRA)")

    def generate(self):
        tc = AutotoolsToolchain(self)
        shared = "1" if self.options.shared else "0"
        not_shared = "1" if not self.options.shared else "0"
        tc.make_args = [
            "PREFIX=/",
            f"BUILD_DYNAMIC_LIB={shared}",
            f"BUILD_STATIC_LIB={not_shared}",
            f"USE_STATIC_LIB={not_shared}",
        ]
        tc.generate()

    def build(self):
        with chdir(self, self.source_folder):
            autotools = Autotools(self)
            autotools.make()

    def package(self):
        copy(self, "COPYING", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "COPYING.LGPL", self.source_folder, os.path.join(self.package_folder, "licenses"))
        with chdir(self, self.source_folder):
            autotools = Autotools(self)
            autotools.install()
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.libs = ["i2c"]
