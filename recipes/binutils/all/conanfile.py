import os
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc, unix_path

required_conan_version = ">=2.4"


class BinutilsConan(ConanFile):
    name = "binutils"
    description = "The GNU Binutils are a collection of binary tools."
    package_type = "application"
    license = "GPL-2.0-or-later"
    homepage = "https://www.gnu.org/software/binutils"
    topics = ("gnu", "ld", "linker", "as", "assembler", "objcopy", "objdump")
    settings = "os", "arch", "compiler", "build_type"

    options = {
        "i18n": [True, False],
        "multilib": [True, False],
        "with_libquadmath": [True, False],
        "target_triplet": [None, "ANY"],
        "prefix": [None, "ANY"],
        "add_unprefixed_to_path": [True, False],
    }
    default_options = {
        "i18n": False,
        "multilib": True,
        "with_libquadmath": True,
        "target_triplet": None,
        "prefix": None,
        "add_unprefixed_to_path": True,
    }
    languages = ["C"]

    python_requires = "conan-gnu-triplet/latest"
    python_requires_extend = "conan-gnu-triplet.TripletMixin"

    def layout(self):
        basic_layout(self, src_folder="src")

    def config_options(self):
        self.options.target_triplet = self.gnu_triplet_target or self.gnu_triplet_host
        self.options.prefix = f"{self.options.target_triplet}-"
        self.output.info(f"binutils:target_triplet={self.options.target_triplet}")

    def validate(self):
        if is_msvc(self):
            raise ConanInvalidConfiguration("MSVC is not supported")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.options.add_unprefixed_to_path

    def build_requirements(self):
        if self.settings_build.os == "Windows":
            self.win_bash = True
            if not self.conf.get("tools.microsoft.bash:path", check_type="str"):
                self.tool_requires("msys2/latest")
        self.tool_requires("bison/[^3.8.2]")
        self.tool_requires("flex/[^2.6.4]")
        if self.options.i18n:
            self.tool_requires("gettext/[>=0.21 <1]", options={"tools": True})

    def requirements(self):
        self.requires("zlib-ng/[^2.0]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        for makefile in Path(self.source_folder).glob("*/Makefile.in"):
            replace_in_file(self, makefile, "install-info-am:", "install-info-am:;\n_disabled_:", strict=False)
            replace_in_file(self, makefile, "INFO_DEPS = ", "INFO_DEPS = # ", strict=False)

    @property
    def _exec_prefix(self):
        return os.path.join("bin", "exec_prefix")

    def generate(self):
        def yes_no(opt): return "yes" if opt else "no"
        tc = AutotoolsToolchain(self)
        tc.configure_args.append(f"--enable-nls={yes_no(self.options.i18n)}")
        tc.configure_args.append(f"--target={self.options.target_triplet}")
        tc.configure_args.append(f"--enable-multilib={yes_no(self.options.multilib)}")
        tc.configure_args.append(f"--with-zlib={unix_path(self, self.dependencies['zlib-ng'].package_folder)}")
        tc.configure_args.append(f"--program-prefix={self.options.prefix}")
        tc.configure_args.append("--exec_prefix=/bin/exec_prefix")
        tc.generate()

    def build(self):
        autotools = Autotools(self)
        autotools.configure()
        autotools.make()

    def package(self):
        autotools = Autotools(self)
        autotools.install()
        if not self.options.i18n:
            rmdir(self, os.path.join(self.package_folder, "share"))
        else:
            rmdir(self, os.path.join(self.package_folder, "share", "man"))
        rm(self, "*.la", os.path.join(self.package_folder, "lib"), recursive=True)
        copy(self, "COPYING*", self.source_folder, os.path.join(self.package_folder, "licenses"), keep_path=False,)

    def package_info(self):
        target_bindir = os.path.join(self._exec_prefix, str(self.options.target_triplet), "bin")
        self.cpp_info.bindirs = ["bin", target_bindir]
        if self.options.i18n:
            self.cpp_info.resdirs = ["share"]

        bindir = os.path.join(self.package_folder, "bin")
        absolute_target_bindir = os.path.join(self.package_folder, target_bindir)
        self.buildenv_info.append_path("PATH", bindir)
        if self.options.add_unprefixed_to_path:
            self.buildenv_info.append_path("PATH", absolute_target_bindir)

        self.conf_info.define("user.binutils:gnu_triplet", str(self.options.target_triplet))
        self.conf_info.define("user.binutils:prefix", str(self.options.prefix))

        self.cpp_info.resdirs = ["etc"]
        self.buildenv_info.define("GPROFNG_SYSCONFDIR", os.path.join(self.package_folder, "etc"))
        if self.settings.os in ("FreeBSD", "Linux"):
            self.cpp_info.system_libs = ["dl", "rt"]
