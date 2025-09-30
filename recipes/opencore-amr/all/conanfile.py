import os

from conan import ConanFile
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.env import Environment, VirtualBuildEnv
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc, unix_path

required_conan_version = ">=2.1"


class OpencoreAmrConan(ConanFile):
    name = "opencore-amr"
    homepage = "https://sourceforge.net/projects/opencore-amr/"
    description = "OpenCORE Adaptive Multi Rate (AMR) speech codec library implementation."
    topics = ("audio-codec", "amr", "opencore")
    license = "Apache-2.0"
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        basic_layout(self, src_folder="src")

    def build_requirements(self):
        if self.settings_build.os == "Windows":
            self.win_bash = True
            if not self.conf.get("tools.microsoft.bash:path", check_type=str):
                self.tool_requires("msys2/latest")
        if is_msvc(self):
            self.tool_requires("automake/[^1.18.1]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        env = VirtualBuildEnv(self)
        env.generate()
        tc = AutotoolsToolchain(self)
        tc.configure_args.extend([
            "--disable-compile-c",
            "--disable-examples",
        ])
        if is_msvc(self):
            tc.extra_cxxflags.append("-EHsc")
        tc.generate()

        if is_msvc(self):
            env = Environment()
            compile_wrapper = unix_path(self, self.conf.get("user.automake:compile-wrapper"))
            ar_wrapper = unix_path(self, self.conf.get("user.automake:lib-wrapper"))
            env.define("CC", f"{compile_wrapper} cl -nologo")
            env.define("CXX", f"{compile_wrapper} cl -nologo")
            env.define("LD", "link -nologo")
            env.define("AR", f"{ar_wrapper} \"lib -nologo\"")
            env.define("NM", "dumpbin -symbols")
            env.define("OBJDUMP", ":")
            env.define("RANLIB", ":")
            env.define("STRIP", ":")
            env.vars(self).save_script("conanbuild_msvc")

    def build(self):
        autotools = Autotools(self)
        autotools.configure()
        autotools.make()

    def package(self):
        copy(self, pattern="LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        autotools = Autotools(self)
        autotools.install()

        rm(self, "*.la", os.path.join(self.package_folder, "lib"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

        fix_apple_shared_install_name(self)

        if is_msvc(self) and self.options.shared:
            for lib in ("opencore-amrwb", "opencore-amrnb"):
                rename(self, os.path.join(self.package_folder, "lib", "{}.dll.lib".format(lib)),
                             os.path.join(self.package_folder, "lib", "{}.lib".format(lib)))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "opencore-amr")
        self.cpp_info.set_property(
            "cmake_target_name", "opencore-amr::opencore-amr")
        for lib in ("opencore-amrwb", "opencore-amrnb"):
            self.cpp_info.components[lib].set_property(
                "cmake_target_name", f'opencore-amr::{lib}')
            self.cpp_info.components[lib].set_property("pkg_config_name", lib)
            self.cpp_info.components[lib].libs = [lib]
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.components[lib].system_libs.extend(["m"])
