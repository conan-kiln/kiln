import os
import re
from pathlib import Path

from conan import ConanFile
from conan.tools.apple import is_apple_os, to_apple_arch
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsToolchain, PkgConfigDeps, AutotoolsDeps
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc

required_conan_version = ">=2.1"


class SwigConan(ConanFile):
    name = "swig"
    description = "SWIG is a software development tool that connects programs written in C and C++ with a variety of high-level programming languages."
    license = "GPL-3.0-or-later"
    homepage = "http://www.swig.org"
    topics = ("python", "java", "wrapper")
    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    def export_sources(self):
        copy(self, "cmake/*", src=self.recipe_folder, dst=self.export_sources_folder)
        export_conandata_patches(self)

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler

    def requirements(self):
        self.requires("pcre2/[^10.42]")
        if is_apple_os(self):
            self.requires("gettext/[>=0.21 <1]")

    def build_requirements(self):
        if not self.conf.get("tools.gnu:pkg_config", default=False, check_type=str):
            self.tool_requires("pkgconf/[>=2.2 <3]")
        if self.settings_build.os == "Windows":
            self.win_bash = True
            if not self.conf.get("tools.microsoft.bash:path", check_type=str):
                self.tool_requires("msys2/latest")
            if is_msvc(self):
                self.tool_requires("cccl/1.3")
        self.tool_requires("bison/[^3.8.2]")
        self.tool_requires("automake/[^1.18.1]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = AutotoolsToolchain(self)
        env = tc.environment()
        tc.configure_args += [
            f"--host={self.settings.arch}",
            "--with-swiglibdir=${prefix}/bin/swiglib",
            "--with-pcre",
        ]
        env.prepend_path("ACLOCAL_PATH", "Tools/config")
        if self.settings.os in ["Linux", "FreeBSD"]:
            tc.configure_args.append("LIBS=-ldl")
            tc.extra_defines.append("HAVE_UNISTD_H=1")
        elif self.settings.os == "Windows":
            if is_msvc(self):
                env.define("CC", "cccl -FS")
                env.define("CXX", "cccl -FS")
                tc.configure_args.append("--disable-ccache")
            else:
                tc.extra_ldflags.append("-static")
                tc.configure_args.append("LIBS=-lmingwex -lssp")
        elif is_apple_os(self):
            tc.extra_cflags.append(f"-arch {to_apple_arch(self)}")
            tc.extra_cxxflags.append(f"-arch {to_apple_arch(self)}")
            tc.extra_ldflags.append(f"-arch {to_apple_arch(self)}")
        tc.generate(env)

        deps = PkgConfigDeps(self)
        deps.generate()

        if is_apple_os(self):
            deps = AutotoolsDeps(self)
            deps.generate()

    def _patch_sources(self):
        # Rely on AutotoolsDeps instead of pcre2-config
        # https://github.com/swig/swig/blob/v4.1.1/configure.ac#L70-L92
        # https://github.com/swig/swig/blob/v4.0.2/configure.ac#L65-L86
        replace_in_file(self, os.path.join(self.source_folder, "configure.ac"),
                        'AS_IF([test "x$with_pcre" != xno],', 'AS_IF([false],')
        configure_ac = Path(self.source_folder, "configure.ac")
        # The project configure.ac looks for TclConfig.sh very stubbornly
        # and provides no config variables to disable it.
        # Configuration fails if Tcl is not present on the system.
        content = configure_ac.read_text()
        content, n = re.subn(r'# Look for Tcl.+AC_SUBST\(TCLINCLUDE\)', r'AC_SUBST(TCLINCLUDE)', content, flags=re.DOTALL | re.MULTILINE)
        assert n == 1, "Failed to disable TCL autodetection in configure.ac"
        configure_ac.write_text(content)

    def build(self):
        self._patch_sources()
        with chdir(self, self.source_folder):
            autotools = Autotools(self)
            autotools.autoreconf()
            autotools.configure()
            autotools.make()

    def package(self):
        copy(self, "LICENSE*", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        copy(self, "COPYRIGHT", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        with chdir(self, self.source_folder):
            autotools = Autotools(self)
            autotools.install()
        copy(self, "*.cmake",
             os.path.join(self.export_sources_folder, "cmake"),
             os.path.join(self.package_folder, self._module_subfolder))

    @property
    def _module_subfolder(self):
        return os.path.join("share", "swig")

    @property
    def _cmake_module_rel_path(self):
        return os.path.join(self._module_subfolder, "conan-swig-variables.cmake")

    def package_info(self):
        self.cpp_info.includedirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.set_property("cmake_file_name", "SWIG")
        self.cpp_info.set_property("cmake_target_name", "SWIG::SWIG")
        self.cpp_info.set_property("cmake_build_modules", [self._cmake_module_rel_path])

        self.buildenv_info.define_path("SWIG_LIB", os.path.join(self.package_folder, "bin", "swiglib"))
