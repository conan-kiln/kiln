import os
from functools import cached_property

from conan import ConanFile
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.build import cross_building
from conan.tools.env import Environment, VirtualRunEnv
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc, unix_path

required_conan_version = ">=2.1"


class NautyConan(ConanFile):
    name = "nauty"
    description = "Graph canonical labeling and automorphism group computation"
    license = "Apache-2.0"
    homepage = "https://pallini.di.uniroma1.it/"
    topics = ("graph-theory", "automorphism", "isomorphism")
    package_type = "static-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "fPIC": [True, False],
        "tools": [True, False],
        "tls": [True, False],
        "wordsize": [16, 32, 64, 128],
        "small": [True, False],
    }
    default_options = {
        "fPIC": True,
        "tools": False,
        "tls": True,
        "wordsize": 64,
        "small": False,
    }
    options_description = {
        "tools": "Build executables",
        "tls": "Enable thread-local storage. Makes the library thread-safe,"
               " but may slow it down slightly if you aren’t using threads.",
        "wordsize": "The size of a single 'setword' in bits."
                    " I.e. how many set elements can be stored by a single setword integer value.",
        "small": "Set the maximum order of a graph to the wordsize value.",
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if "64" in str(self.settings.arch) or self.settings.arch in ["armv8", "armv8.3"]:
            self.options.wordsize = 64
        else:
            self.options.wordsize = 32

    @cached_property
    def _libname(self):
        libname = "nauty"
        if self.options.tls:
            libname += "T"
        libname += {16: "S", 32: "W", 64: "L", 128: "Q"}[int(self.options.wordsize.value)]
        if self.options.small:
            libname += "1"
        return libname

    def layout(self):
        basic_layout(self, src_folder="src")

    def build_requirements(self):
        if not self.conf.get("tools.gnu:pkg_config", check_type=str):
            self.tool_requires("pkgconf/[^2.2]")
        if self.settings_build.os == "Windows":
            self.win_bash = True
            if not self.conf.get("tools.microsoft.bash:path", check_type=str):
                self.tool_requires("msys2/latest")
            if is_msvc(self):
                self.tool_requires("automake/[^1.18.1]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        if not cross_building(self):
            VirtualRunEnv(self).generate(scope="build")
        tc = AutotoolsToolchain(self)
        tc.configure_args.extend([
            "--enable-generic",  # no -march=native
            "--enable-tls" if self.options.tls else "--disable-tls",
        ])
        if not self.options.tools:
            tc.make_args.append("GTOOLS=")
        if self.options.tls:
            tc.make_args.append("GLIBS=")
            tc.make_args.append(f"TLSLIBS=lib{self._libname}.la")
        else:
            tc.make_args.append(f"GLIBS=lib{self._libname}.la")
            tc.make_args.append("TLSLIBS=")
        tc.generate()

        if is_msvc(self):
            env = Environment()
            automake_conf = self.dependencies.build["automake"].conf_info
            compile_wrapper = unix_path(self, automake_conf.get("user.automake:compile-wrapper", check_type=str))
            ar_wrapper = unix_path(self, automake_conf.get("user.automake:lib-wrapper", check_type=str))
            env.define("CC", f"{compile_wrapper} cl -nologo")
            env.define("CXX", f"{compile_wrapper} cl -nologo")
            env.define("LD", "link -nologo")
            env.define("AR", f"{ar_wrapper} lib")
            env.define("NM", "dumpbin -symbols")
            env.vars(self).save_script("conanbuild_msvc")

    def build(self):
        if not self.options.tools:
            replace_in_file(self, os.path.join(self.source_folder, "makefile.in"),
                            "${INSTALL} ${GTOOLS} ${DESTDIR}${bindir}", "")
        if self.options.tls:
            replace_in_file(self, os.path.join(self.source_folder, "makefile.in"),
                            "${LIBTOOL} --mode=install ${INSTALL} ${GLIBS}", "# ")
        with chdir(self, self.source_folder):
            autotools = Autotools(self)
            autotools.configure()
            autotools.make()
            if self.options.tls:
                autotools.make(target="TLSlibs")

    def package(self):
        copy(self, "COPYRIGHT", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "LICENSE-2.0.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        with chdir(self, self.source_folder):
            autotools = Autotools(self)
            autotools.install()
            if self.options.tls:
                autotools.install(target="TLSinstall")
        rm(self, "*.la", os.path.join(self.package_folder, "lib"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        fix_apple_shared_install_name(self)

    def package_info(self):
        self.cpp_info.set_property("cmake_target_aliases", ["nauty", self._libname])
        self.cpp_info.set_property("pkg_config_name", self._libname)
        self.cpp_info.set_property("pkg_config_aliases", ["nauty"])
        self.cpp_info.libs = [self._libname]
        self.cpp_info.defines = [f"WORDSIZE={self.options.wordsize}"]
        if self.options.small:
            self.cpp_info.defines.append("MAXN=WORDSIZE")
        if self.options.tls:
            self.cpp_info.defines.append("USE_TLS")
