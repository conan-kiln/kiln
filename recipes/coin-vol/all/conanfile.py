import os

from conan import ConanFile
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsToolchain, PkgConfigDeps
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc, msvc_runtime_flag

required_conan_version = ">=2.1"


class VolConan(ConanFile):
    name = "coin-vol"
    description = "Volume Algorithm for solving large-scale linear programming problems"
    license = "EPL-2.0"
    homepage = "https://github.com/coin-or/Vol"
    topics = ("linear-programming", "optimization", "volume-algorithm", "coin-or")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_osi": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_osi": True,
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("coin-utils/[^2.11.11]")
        if self.options.with_osi:
            self.requires("coin-osi/[>=0.108 <1]", transitive_headers=True)

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
        def yes_no(v):
            return "yes" if v else "no"
        tc = AutotoolsToolchain(self)
        tc.configure_args.append("--with-coinutils")
        tc.configure_args.append(f"--with-osi={yes_no(self.options.with_osi)}")
        if is_msvc(self):
            tc.extra_cxxflags.append("-EHsc")
            tc.configure_args.append(f"--enable-msvc={msvc_runtime_flag(self)}")
        env = tc.environment()
        env.define("PKG_CONFIG_PATH", self.generators_folder)
        if is_msvc(self):
            env.define("CC", "cl -nologo")
            env.define("CXX", "cl -nologo")
            env.define("LD", "link -nologo")
            env.define("AR", "lib -nologo")
        tc.generate(env)

        deps = PkgConfigDeps(self)
        deps.generate()

    def build(self):
        buildtools = self.dependencies.build["coin-buildtools"].cpp_info.resdirs[0]
        copy(self, "*", buildtools, os.path.join(self.source_folder, "Vol", "BuildTools"))
        for gnu_config in [
            self.conf.get("user.gnu-config:config_guess", check_type=str),
            self.conf.get("user.gnu-config:config_sub", check_type=str),
        ]:
            if gnu_config:
                copy(self, os.path.basename(gnu_config), src=os.path.dirname(gnu_config), dst=self.source_folder)
        autotools = Autotools(self)
        autotools.autoreconf(build_script_folder="Vol")
        autotools.configure(build_script_folder="Vol")
        autotools.make()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        autotools = Autotools(self)
        autotools.install(args=["-j1"])
        rm(self, "*.la", os.path.join(self.package_folder, "lib"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        fix_apple_shared_install_name(self)

    def package_info(self):
        self.cpp_info.components["vol"].set_property("pkg_config_name", "vol")
        self.cpp_info.components["vol"].libs = ["Vol"]
        self.cpp_info.components["vol"].includedirs = ["include", "include/coin"]
        self.cpp_info.components["vol"].requires = ["coin-utils::coin-utils"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["vol"].system_libs = ["m"]

        if self.options.with_osi:
            self.cpp_info.components["osi-vol"].set_property("pkg_config_name", "osi-vol")
            self.cpp_info.components["osi-vol"].libs = ["OsiVol"]
            self.cpp_info.components["osi-vol"].requires = ["vol", "coin-osi::coin-osi"]
