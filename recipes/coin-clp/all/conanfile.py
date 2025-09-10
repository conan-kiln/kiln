import os
import shutil

from conan import ConanFile
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsToolchain, PkgConfigDeps, AutotoolsDeps
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc, unix_path, msvc_runtime_flag

required_conan_version = ">=2.1"


class CoinClpConan(ConanFile):
    name = "coin-clp"
    description = "COIN-OR Linear Programming Solver"
    topics = ("clp", "simplex", "solver", "linear", "programming")
    homepage = "https://github.com/coin-or/Clp"
    license = "EPL-2.0"
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "enable_aboca": [True, False],
        "aboca_inherit": [True, False],
        "with_cholmod": [True, False],
        "with_amd": [True, False],
        "with_glpk": [True, False],
        "with_asl": [True, False],
        "with_mumps": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "enable_aboca": False,
        "aboca_inherit": False,
        "with_cholmod": True,  # LGPL
        "with_amd": False,     # BSD
        "with_glpk": False,    # GPL
        "with_asl": False,     # BSD
        "with_mumps": False,   # CeCILL
    }
    implements = ["auto_shared_fpic"]

    def configure(self):
        if self.options.shared:
            del self.options.fPIC
        if not self.options.enable_aboca:
            del self.options.aboca_inherit
        if self.options.with_glpk:
            # Can't use GLPK without AMD or CHOLMOD
            self.options.with_amd.value = True
        if self.options.with_cholmod:
            # AMD is a transitive dep of CHOLMOD anyway
            self.options.with_amd.value = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        # Symbols are exposed https://github.com/conan-io/conan-center-index/pull/16053#issuecomment-1512637106
        self.requires("coin-utils/[^2.11.11]", transitive_headers=True, transitive_libs=True)
        self.requires("coin-osi/[>=0.108.10 <1]", transitive_headers=True)
        if self.options.with_asl:
            self.requires("ampl-asl/[^1]")
        if self.options.with_glpk:
            self.requires("glpk/[<=4.48]")
        if self.options.with_mumps:
            self.requires("coin-mumps/[^3.0.5]")
        if self.options.with_amd:
            self.requires("suitesparse-amd/[^3.3.2]")
        if self.options.with_cholmod:
            self.requires("suitesparse-cholmod/[^5.2.1]")

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
        yes_no = lambda v: "yes" if v else "no"
        tc = AutotoolsToolchain(self)
        tc.configure_args.extend([
            f"--with-asl={yes_no(self.options.with_asl)}",
            f"--with-glpk={yes_no(self.options.with_glpk)}",
            f"--with-mumps={yes_no(self.options.with_mumps)}",
            f"--with-mumps={yes_no(self.options.with_mumps)}",
            f"--enable-amd-libcheck={yes_no(self.options.with_amd)}",
            f"--enable-cholmod-libcheck={yes_no(self.options.with_cholmod)}",
            "--without-wsmp",
            "--without-metis",  # not really used
            # These are only used for sample datasets
            "--without-netlib",
            "--without-sample",
            "--disable-dependency-linking",
            "F77=unavailable",
        ])

        def _libflags(name):
            dep_info = self.dependencies[name].cpp_info.aggregated_components()
            flags = [f"-L{unix_path(self, lib)}" for lib in dep_info.libdirs]
            flags += [f"-l{lib}" for lib in dep_info.libs]
            flags += [f"-l{lib}" for lib in dep_info.system_libs]
            return " ".join(flags)

        def _configure_dep(opt_name, dep):
            inc_dir = self.dependencies[dep].cpp_info.includedirs[0]
            if dep.startswith("suitesparse"):
                inc_dir = os.path.join(inc_dir, "suitesparse")
            tc.configure_args.append(f"--with-{opt_name}-incdir={unix_path(self, inc_dir)}")
            tc.configure_args.append(f"--with-{opt_name}-lib={_libflags(dep)}")

        if self.options.with_asl:
            _configure_dep("asl", "ampl-asl")
        if self.options.with_glpk:
            _configure_dep("glpk", "glpk")
        if self.options.with_mumps:
            _configure_dep("mumps", "coin-mumps")
        if self.options.with_amd:
            _configure_dep("amd", "suitesparse-amd")
        if self.options.with_cholmod:
            _configure_dep("cholmod", "suitesparse-cholmod")

        # TODO: package Cilk for parallelization support in the Aboca solver
        if self.options.enable_aboca:
            tc.configure_args.append(f"--enable-aboca={2 if self.options.aboca_inherit else 1}")
        else:
            tc.configure_args.append("--disable-aboca")

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
            env.define("AR", f"{ar_wrapper} \"lib -nologo\"")
            env.define("NM", "dumpbin -symbols")
        tc.generate(env)

        deps = PkgConfigDeps(self)
        deps.set_property("openblas", "pkg_config_aliases", ["coinblas", "coinlapack"])
        deps.set_property("ampl-asl::asl2-mt", "pkg_config_aliases", ["coinasl"])
        deps.set_property("glpk", "pkg_config_aliases", ["coinglpk"])
        deps.generate()

        deps = AutotoolsDeps(self)
        deps.generate()

    def build(self):
        buildtools = self.dependencies.build["coin-buildtools"].cpp_info.resdirs[0]
        copy(self, "*", buildtools, os.path.join(self.source_folder, "Clp", "BuildTools"))
        for gnu_config in ["config_guess", "config_sub"]:
            gnu_config = self.conf.get(f"user.gnu-config:{gnu_config}", check_type=str)
            shutil.copy(gnu_config, os.path.join(self.source_folder, "Clp"))
        autotools = Autotools(self)
        autotools.autoreconf(build_script_folder="Clp")
        autotools.configure(build_script_folder="Clp")
        autotools.make()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        # Installation script expects include/coin to already exist
        mkdir(self, os.path.join(self.package_folder, "include", "coin"))
        autotools = Autotools(self)
        autotools.install(args=["-j1"])
        rm(self, "*.la", os.path.join(self.package_folder, "lib"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        fix_apple_shared_install_name(self)
        if is_msvc(self):
            for l in ("Clp", "ClpSolver", "OsiClp"):
                rename(self, os.path.join(self.package_folder, "lib", f"lib{l}.a"),
                             os.path.join(self.package_folder, "lib", f"{l}.lib"))

    def package_info(self):
        self.cpp_info.components["clp"].set_property("pkg_config_name", "clp")
        self.cpp_info.components["clp"].libs = ["Clp"]
        self.cpp_info.components["clp"].includedirs.append("include/coin")
        self.cpp_info.components["clp"].requires = [
            "solver",
            "coin-utils::coin-utils",
        ]
        if self.options.with_mumps:
            self.cpp_info.components["clp"].requires.append("coin-mumps::coin-mumps")
        if self.options.with_amd:
            self.cpp_info.components["clp"].requires.append("suitesparse-amd::suitesparse-amd")
        if self.options.with_cholmod:
            self.cpp_info.components["clp"].requires.append("suitesparse-cholmod::suitesparse-cholmod")

        self.cpp_info.components["solver"].set_property("pkg_config_name", "clp-solver")
        self.cpp_info.components["solver"].libs = ["Clp"]
        self.cpp_info.components["solver"].includedirs.append("include/coin")
        self.cpp_info.components["solver"].requires = ["coin-utils::coin-utils"]
        if self.options.with_asl:
            self.cpp_info.components["solver"].requires.append("ampl-asl::asl2-mt")
        if self.options.with_glpk:
            self.cpp_info.components["solver"].requires.append("glpk::glpk")

        self.cpp_info.components["osi-clp"].set_property("pkg_config_name", "osi-clp")
        self.cpp_info.components["osi-clp"].libs = ["OsiClp"]
        self.cpp_info.components["osi-clp"].requires = ["clp", "coin-osi::coin-osi"]
