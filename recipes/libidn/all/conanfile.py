import os

from conan import ConanFile
from conan.tools.build import cross_building
from conan.tools.env import VirtualRunEnv, Environment
from conan.tools.files import *
from conan.tools.gnu import AutotoolsToolchain, Autotools, AutotoolsDeps
from conan.tools.layout import basic_layout
from conan.tools.microsoft import unix_path, is_msvc

required_conan_version = ">=2.4"


class LibIdnConan(ConanFile):
    name = "libidn"
    description = "GNU Libidn is a fully documented implementation of the Stringprep, Punycode and IDNA 2003 specifications."
    homepage = "https://www.gnu.org/software/libidn/"
    topics = ("libidn", "encode", "decode", "internationalized", "domain", "name")
    license = "GPL-3.0-or-later"

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "i18n": [True, False],
        "threads": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "i18n": False,
        "threads": True,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("libiconv/[^1.17]")

    def build_requirements(self):
        if self.settings_build.os == "Windows":
            self.win_bash = True
            if not self.conf.get("tools.microsoft.bash:path", check_type=str):
                self.tool_requires("msys2/latest")
        if is_msvc(self):
            self.tool_requires("automake/[^1.18.1]")
        if self.options.i18n:
            self.tool_requires("gettext/[>=0.21 <1]", options={"tools": True})

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        if not cross_building(self):
            env = VirtualRunEnv(self)
            env.generate(scope="build")

        tc = AutotoolsToolchain(self)
        if not self.options.shared:
            tc.extra_defines.append("LIBIDN_STATIC")
        yes_no = lambda v: "yes" if v else "no"
        tc.configure_args += [
            f"--enable-threads={yes_no(self.options.threads)}",
            f"--with-libiconv-prefix={unix_path(self, self.dependencies['libiconv'].package_folder)}",
            f"--enable-nls={yes_no(self.options.i18n)}",
            "--disable-csharp",
            "--disable-rpath",
        ]
        tc.generate()

        if is_msvc(self):
            env = Environment()
            dep_info = self.dependencies["libiconv"].cpp_info.aggregated_components()
            env.append("CPPFLAGS", [f"-I{unix_path(self, p)}" for p in dep_info.includedirs] + [f"-D{d}" for d in dep_info.defines])
            env.append("_LINK_", [lib if lib.endswith(".lib") else f"{lib}.lib" for lib in (dep_info.libs + dep_info.system_libs)])
            env.append("LDFLAGS", [f"-L{unix_path(self, p)}" for p in dep_info.libdirs] + dep_info.sharedlinkflags + dep_info.exelinkflags)
            env.append("CFLAGS", dep_info.cflags)
            env.vars(self).save_script("conanautotoolsdeps_cl_workaround")
        else:
            deps = AutotoolsDeps(self)
            deps.generate()

        if is_msvc(self):
            env = Environment()
            compile_wrapper = unix_path(self, self.conf.get("user.automake:compile-wrapper"))
            ar_wrapper = unix_path(self, self.conf.get("user.automake:lib-wrapper"))
            # Workaround for iconv.lib not being found due to linker flag order
            libiconv_libdir = unix_path(self, self.dependencies["libiconv"].cpp_info.aggregated_components().libdir)
            env.define("CC", f"{compile_wrapper} cl -nologo -L{libiconv_libdir}")
            env.define("CXX", f"{compile_wrapper} cl -nologo")
            env.define("LD", "link -nologo")
            env.define("AR", f'{ar_wrapper} lib')
            env.vars(self).save_script("conanbuild_msvc")

    def _patch_sources(self):
        # Disable examples and tests
        for subdir in ["examples", "tests", "fuzz", "gltests", os.path.join("lib", "gltests"), "doc"]:
            save(self, os.path.join(self.source_folder, subdir, "Makefile.in"), "all:\ninstall:\n")

        if is_msvc(self):
            if self.settings.arch in ("x86_64", "armv8", "armv8.3"):
                ssize = "signed long long int"
            else:
                ssize = "signed long int"
            replace_in_file(self, os.path.join(self.source_folder, "lib", "stringprep.h"), "ssize_t", ssize)

        if self.settings.os == "Windows":
            # Otherwise tries to create a symlink from GNUmakefile to itself, which fails on Windows
            replace_in_file(self, os.path.join(self.source_folder, "configure"),
                            '"$GNUmakefile") CONFIG_LINKS="$CONFIG_LINKS $GNUmakefile:$GNUmakefile" ;;', "")
            replace_in_file(self, os.path.join(self.source_folder, "configure"),
                            'ac_config_links="$ac_config_links $GNUmakefile:$GNUmakefile"', "")

    def build(self):
        self._patch_sources()
        autotools = Autotools(self)
        autotools.configure()
        autotools.make()

    def package(self):
        copy(self, "COPYING", self.source_folder, os.path.join(self.package_folder, "licenses"))
        autotools = Autotools(self)
        autotools.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rm(self, "*.la", os.path.join(self.package_folder, "lib"), recursive=True)

        if is_msvc(self) and self.options.shared:
            os.rename(os.path.join(self.package_folder, "lib", "idn.dll.lib"),
                      os.path.join(self.package_folder, "lib", "idn-12.lib"))

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "libidn")
        if is_msvc(self) and self.options.shared:
            self.cpp_info.libs = ["idn-12"]
        else:
            self.cpp_info.libs = ["idn"]
        self.cpp_info.resdirs = ["share"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            if self.options.threads:
                self.cpp_info.system_libs = ["pthread"]
        if self.settings.os == "Windows":
            if not self.options.shared:
                self.cpp_info.defines = ["LIBIDN_STATIC"]
