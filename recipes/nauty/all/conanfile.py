import os

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
        "enable_tls": [True, False],
        "tools": [True, False],
    }
    default_options = {
        "fPIC": True,
        "enable_tls": False,
        "tools": False,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

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
            "--enable-tls" if self.options.enable_tls else "--disable-tls",
        ])
        if not self.options.tools:
            tc.make_args.append("GTOOLS=")
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
        with chdir(self, self.source_folder):
            autotools = Autotools(self)
            autotools.configure()
            autotools.make()
            if self.options.enable_tls:
                autotools.make(target="TLSlibs")

    def package(self):
        copy(self, "COPYRIGHT", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "LICENSE-2.0.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        with chdir(self, self.source_folder):
            autotools = Autotools(self)
            autotools.install()
            if self.options.enable_tls:
                autotools.install(target="TLSinstall")
        rm(self, "*.la", os.path.join(self.package_folder, "lib"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        fix_apple_shared_install_name(self)

    def package_info(self):
        def add_component(name, defines):
            self.cpp_info.components[name].set_property("pkg_config_name", name)
            self.cpp_info.components[name].libs = [name]
            self.cpp_info.components[name].defines = defines

            if self.options.enable_tls:
                name = name.replace("nauty", "nautyT")
                self.cpp_info.components[name].set_property("pkg_config_name", name)
                self.cpp_info.components[name].libs = [name]
                self.cpp_info.components[name].defines = defines + ["USE_TLS"]

        add_component("nauty", [])
        add_component("nauty1", ["MAXN=WORDSIZE"])
        add_component("nautyL1", ["WORDSIZE=64", "MAXN=WORDSIZE"])
        add_component("nautyL", ["WORDSIZE=64"])
        add_component("nautyQ1", ["WORDSIZE=128", "MAXN=WORDSIZE"])
        add_component("nautyQ", ["WORDSIZE=128"])
        add_component("nautyS1", ["WORDSIZE=16", "MAXN=WORDSIZE"])
        add_component("nautyS", ["WORDSIZE=16"])
        add_component("nautyW1", ["WORDSIZE=32", "MAXN=WORDSIZE"])
        add_component("nautyW", ["WORDSIZE=32"])
