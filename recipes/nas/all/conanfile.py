import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import can_run
from conan.tools.files import *
from conan.tools.gnu import AutotoolsToolchain, Autotools, AutotoolsDeps
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class NasRecipe(ConanFile):
    name = "nas"
    description = "The Network Audio System is a network transparent, client/server audio transport system."
    topics = ("audio", "sound")
    homepage = "https://www.radscan.com/nas.html"
    license = "DocumentRef-wave.h:LicenseRef-MIT-advertising"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    def layout(self):
        basic_layout(self, src_folder="src")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def export_sources(self):
        export_conandata_patches(self)

    def validate(self):
        if self.settings.os not in ("FreeBSD", "Linux"):
            raise ConanInvalidConfiguration("Recipe supports Linux only")
        if self.settings.compiler == "clang":
            # See https://github.com/conan-io/conan-center-index/pull/16267#issuecomment-1469824504
            raise ConanInvalidConfiguration("Recipe cannot be built with clang")

    def requirements(self):
        self.requires("xorg/system")

    def build_requirements(self):
        self.tool_requires("bison/[^3.8.2]")
        self.tool_requires("flex/[^2.6.4]")
        self.tool_requires("imake/1.0.9")
        self.tool_requires("xorg-cf-files/1.0.8")
        self.tool_requires("xorg-makedepend/1.0.8")
        self.tool_requires("xorg-gccmakedep/1.0.3")
        self.tool_requires("gnu-config/[*]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version][0],  strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = AutotoolsToolchain(self)
        env = tc.environment()
        env.prepend_path("PATH", self.source_folder)
        deps_vars = AutotoolsDeps(self).environment.vars(self)
        tc_vars = tc.vars()
        tc.make_args.append(f"CCOPTIONS={deps_vars['CPPFLAGS']} {tc_vars['CFLAGS']}")
        tc.make_args.append(f"EXTRA_LDOPTIONS={deps_vars['LDFLAGS']} {deps_vars['LIBS']}")
        tc.make_args.append(f"SHLIBGLOBALSFLAGS={deps_vars['LDFLAGS']} {deps_vars['LIBS']}")
        tc.make_args.append("CDEBUGFLAGS=")
        tc.generate(env)

    @property
    def _imake_irulesrc(self):
        return self.conf.get("user.xorg-cf-files:config-path")

    @property
    def _imake_defines(self):
        return f"-DUsrLibDir={os.path.join(self.package_folder, 'lib')}"

    @property
    def _imake_make_args(self):
        return [f"IRULESRC={self._imake_irulesrc}", f"IMAKE_DEFINES={self._imake_defines}"]

    def build(self):
        for gnu_config in [
            self.conf.get("user.gnu-config:config_guess", check_type=str),
            self.conf.get("user.gnu-config:config_sub", check_type=str),
        ]:
            if gnu_config:
                config_folder = os.path.join(self.source_folder, "config")
                copy(self, os.path.basename(gnu_config), src=os.path.dirname(gnu_config), dst=config_folder)

        with chdir(self, self.source_folder):
            autotools = Autotools(self)

            # imake is hard-coded to use gcc, so we need to alias it to the correct compiler instead
            build_cc = AutotoolsToolchain(self).vars().get("CC_FOR_BUILD" if not can_run(self) else "CC", "cc")
            save(self, "gcc", f'#!/bin/sh\nexec {build_cc} "$@"')
            os.chmod("gcc", 0o755)

            # generate Makefiles
            configure_args = " ".join(AutotoolsToolchain(self).configure_args)
            replace_in_file(self, os.path.join(self.source_folder, "config", "Imakefile"),
                            '\tsh -c "unset CFLAGS LDFLAGS; ./configure"',
                            f'\tsh -c "unset CFLAGS LDFLAGS LIBS; ./configure {configure_args} ac_cv_func_setpgrp_void=yes"')
            self.run(f"CC={build_cc} imake -DUseInstalled -I{self._imake_irulesrc} {self._imake_defines}", shell=True)
            autotools.make(target="Makefiles", args=["-j1"] + self._imake_make_args)
            replace_in_file(self, os.path.join(self.source_folder, "Makefile"),
                            "$(MAKE) $(MFLAGS) Makefiles", "")

            # build using the correct CC
            cc = AutotoolsToolchain(self).vars()["CC"]
            save(self, "gcc", f'#!/bin/sh\nexec {cc} "$@"')
            # j1 avoids some errors while trying to run this target
            autotools.make(target="World", args=["-j1"] + self._imake_make_args)

    def _extract_license(self):
        header = "Copyright 1995"
        footer = "Translation:  You can do whatever you want with this software!"
        nas_audio = load(self, os.path.join(self.source_folder, "README"))
        begin = nas_audio.find(header)
        end = nas_audio.find(footer, begin)
        return nas_audio[begin:end]

    def package(self):
        save(self, os.path.join(self.package_folder, "licenses", "LICENSE"), self._extract_license())

        tmp_install = os.path.join(self.build_folder, "prefix")
        self.output.warning(tmp_install)
        install_args = [
                        f"DESTDIR={tmp_install}",
                        "INCDIR=/include",
                        "ETCDIR=/etc",
                        "USRLIBDIR=/lib",
                        "BINDIR=/bin",
                    ] + self._imake_make_args
        with chdir(self, self.source_folder):
            autotools = Autotools(self)
            # j1 avoids some errors while trying to install
            autotools.install(args=["-j1"] + install_args)

        copy(self, "*", src=os.path.join(tmp_install, "bin"), dst=os.path.join(self.package_folder, "bin"))
        copy(self, "*.h", src=os.path.join(tmp_install, "include"), dst=os.path.join(self.package_folder, "include", "audio"))
        copy(self, "*", src=os.path.join(tmp_install, "lib"), dst=os.path.join(self.package_folder, "lib"))

        # Both are present in the final build and there does not seem to be an obvious way to tell the build system
        # to only generate one of them, so remove the unwanted one
        if self.options.shared:
            rm(self, "*.a", os.path.join(self.package_folder, "lib"))
        else:
            rm(self, "*.so*", os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.libs = ["audio"]
        self.cpp_info.requires = [
            "xorg::x11",
            "xorg::xau",
            "xorg::xcb",
            "xorg::xdmcp",
        ]
