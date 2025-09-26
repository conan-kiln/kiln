import os
import shutil

from conan import ConanFile
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsToolchain, PkgConfigDeps, PkgConfig
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc, msvc_runtime_flag, unix_path

required_conan_version = ">=2.1"


class BonminConan(ConanFile):
    name = "coin-bonmin"
    description = "Bonmin: Basic Open-source Nonlinear Mixed Integer programming"
    license = "EPL-2.0"
    homepage = "https://github.com/coin-or/Bonmin"
    topics = ("optimization", "mixed-integer-nonlinear-programming", "coin-or")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "tools": [True, False],
        "with_asl": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "tools": False,
        "with_asl": False,
    }
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("coin-cbc/[^2.10.12]")
        self.requires("coin-clp/[^1.17.9]")
        self.requires("coin-ipopt/[^3.14.19]", transitive_headers=True, transitive_libs=True)
        if self.options.with_asl:
            self.requires("ampl-asl/[^1]")
        # Optionally also supports FilterSQP commercial software

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

    def _flags_from_pc(self, name):
        pc = PkgConfig(self, name, self.generators_folder)
        cflags = list(pc.cflags)
        cflags += [f"-I{unix_path(self, inc)}" for inc in pc.includedirs]
        ldflags = list(pc.linkflags)
        ldflags += [f"-L{unix_path(self, libdir)}" for libdir in pc.libdirs]
        ldflags += [f"-l{lib}" for lib in pc.libs]
        return " ".join(cflags), " ".join(ldflags)

    def generate(self):
        deps = PkgConfigDeps(self)
        deps.set_property("ampl-asl", "pkg_config_name", "coinasl")
        deps.generate()

        tc = AutotoolsToolchain(self)
        yes_no = lambda v: "yes" if v else "no"
        osi = self.dependencies["coin-osi"]
        tc.configure_args += [
            f"--with-asl={yes_no(self.options.with_asl)}",
            f"--with-osicplex={yes_no(osi.options.with_cplex)}",
            "--with-coinfiltersqp=no",
            "F77=unavailable",
        ]

        if osi.options.with_cplex:
            _, ldflags = self._flags_from_pc("cplex")
            tc.configure_args.append(f"--with-cplex-incdir={unix_path(self, self.dependencies['cplex'].cpp_info.includedir)}/ilcplex")
            tc.configure_args.append(f"--with-cplex-lib={ldflags}")

        if is_msvc(self):
            tc.extra_cxxflags.append("-EHsc")
            tc.configure_args.append(f"--enable-msvc={msvc_runtime_flag(self)}")
        tc.generate()

        env = tc.environment()
        env.define("PKG_CONFIG_PATH", self.generators_folder)
        if is_msvc(self):
            compile_wrapper = unix_path(self, self.conf.get("user.automake:compile-wrapper"))
            ar_wrapper = unix_path(self, self.conf.get("user.automake:lib-wrapper"))
            env.define("CC", f"{compile_wrapper} cl -nologo")
            env.define("CXX", f"{compile_wrapper} cl -nologo")
            env.define("LD", "link -nologo")
            env.define("AR", f"{ar_wrapper} lib")
            env.define("NM", "dumpbin -symbols")
            env.vars(self).save_script("conanbuild_msvc")
        tc.generate(env)

    def build(self):
        buildtools = self.dependencies.build["coin-buildtools"].cpp_info.resdirs[0]
        copy(self, "*", buildtools, os.path.join(self.source_folder, "Bonmin", "BuildTools"))
        for gnu_config in ["config_guess", "config_sub"]:
            gnu_config = self.conf.get(f"user.gnu-config:{gnu_config}", check_type=str)
            shutil.copy(gnu_config, os.path.join(self.source_folder, "Bonmin"))
        autotools = Autotools(self)
        autotools.autoreconf(build_script_folder="Bonmin")
        autotools.configure(build_script_folder="Bonmin")
        autotools.make()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        # Installation script expects include/coin to already exist
        mkdir(self, os.path.join(self.package_folder, "include", "coin"))
        autotools = Autotools(self)
        autotools.install()
        rm(self, "*.la", os.path.join(self.package_folder, "lib"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        if not self.options.tools:
            suffix = ".exe" if self.settings.os == "Windows" else ""
            rm(self, "bonmin" + suffix, os.path.join(self.package_folder, "bin"))

    def package_info(self):
        self.cpp_info.components["libbonmin"].set_property("pkg_config_name", "bonmin")
        self.cpp_info.components["libbonmin"].libs = ["bonmin"]
        self.cpp_info.components["libbonmin"].includedirs.append("include/coin")
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["libbonmin"].system_libs = ["m", "pthread", "rt", "dl"]
        self.cpp_info.components["libbonmin"].requires = [
            "coin-cbc::coin-cbc",
            "coin-clp::coin-clp",
            "coin-ipopt::coin-ipopt",
        ]

        if self.options.with_asl:
            self.cpp_info.components["bonminamplinterface"].set_property("pkg_config_name", "bonminamplinterface")
            self.cpp_info.components["bonminamplinterface"].libs = ["bonminampl"]
            self.cpp_info.components["bonminamplinterface"].includedirs.append("include/coin")
            self.cpp_info.components["bonminamplinterface"].requires = ["libbonmin", "ampl-asl::asl"]
