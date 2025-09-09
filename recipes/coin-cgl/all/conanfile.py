import os

from conan import ConanFile
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsToolchain, PkgConfigDeps
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc, msvc_runtime_flag, unix_path

required_conan_version = ">=2.1"


class CoinCglConan(ConanFile):
    name = "coin-cgl"
    description = "COIN-OR Cut Generator Library"
    topics = ("cgl", "simplex", "solver", "linear", "programming")
    homepage = "https://github.com/coin-or/Cgl"
    license = "EPL-2.0"
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_glpk": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_glpk": True,
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("coin-utils/[^2.11.11]")
        self.requires("coin-osi/[>=0.108.10 <1]")
        self.requires("coin-clp/[^1.17.9]")
        if self.options.with_glpk:
            self.requires("glpk/[<=4.48]")
        # TODO: add support for: Cplex, Mosek, Xpress, Vol, DyLP

    def build_requirements(self):
        self.tool_requires("coin-buildtools/[*]")
        self.tool_requires("gnu-config/[*]")
        if not self.conf.get("tools.gnu:pkg_config", check_type=str):
            self.tool_requires("pkgconf/[>=2.2 <3]")
        if self.settings_build.os == "Windows":
            self.win_bash = True
            if not self.conf.get("tools.microsoft.bash:path", check_type=str):
                self.tool_requires("msys2/latest")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = AutotoolsToolchain(self)
        tc.configure_args.extend([
            "--with-osiglpk" if self.options.with_glpk else "--without-osiglpk",
            "--without-vol",
            "--without-dylp",
            "--without-osicpx",
            "--without-osimsk",
            "--without-osixpr",
            "--without-osivol",
            "--without-sample",
            "--disable-dependency-linking",
            "F77=unavailable",
        ])
        if is_msvc(self):
            tc.extra_cxxflags.append("-EHsc")
            tc.configure_args.append(f"--enable-msvc={msvc_runtime_flag(self)}")
        env = tc.environment()
        env.define("PKG_CONFIG_PATH", self.generators_folder)
        if is_msvc(self):
            compile_wrapper = unix_path(self, self.conf.get("user.automake:compile-wrapper", check_type=str))
            ar_wrapper = unix_path(self, self.conf.get("user.automake:lib-wrapper", check_type=str))
            env.define("CC", f"{compile_wrapper} cl -nologo")
            env.define("CXX", f"{compile_wrapper} cl -nologo")
            env.define("LD", f"{compile_wrapper} link -nologo")
            env.define("AR", f'{ar_wrapper} "lib -nologo"')
            env.define("NM", "dumpbin -symbols")
        tc.generate(env)

        deps = PkgConfigDeps(self)
        deps.set_property("glpk", "pkg_config_aliases", ["coinglpk"])
        deps.generate()

    def build(self):
        copy(self, "*", self.dependencies.build["coin-buildtools"].cpp_info.resdirs[0],
             os.path.join(self.source_folder, "Cgl", "BuildTools"))
        for gnu_config in [
            self.conf.get("user.gnu-config:config_guess", check_type=str),
            self.conf.get("user.gnu-config:config_sub", check_type=str),
        ]:
            copy(self, os.path.basename(gnu_config), src=os.path.dirname(gnu_config), dst=self.source_folder)
        autotools = Autotools(self)
        autotools.autoreconf(build_script_folder="Cgl")
        autotools.configure(build_script_folder="Cgl")
        autotools.make()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        autotools = Autotools(self)
        autotools.install(args=["-j1"])
        rm(self, "*.la", os.path.join(self.package_folder, "lib"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        fix_apple_shared_install_name(self)
        if is_msvc(self):
            rename(self,
                   os.path.join(self.package_folder, "lib", "libCgl.a"),
                   os.path.join(self.package_folder, "lib", "Cgl.lib"))

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "cgl")
        self.cpp_info.libs = ["Cgl"]
        self.cpp_info.includedirs.append(os.path.join("include", "coin"))
