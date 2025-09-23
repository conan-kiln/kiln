import os
import textwrap
from pathlib import Path

from conan import ConanFile
from conan.tools.build import cross_building
from conan.tools.cmake import cmake_layout
from conan.tools.env import Environment
from conan.tools.files import *
from conan.tools.gnu import GnuToolchain

required_conan_version = ">=2.1"


class RumocaConan(ConanFile):
    name = "rumoca"
    description = "A Modelica translator with focus on CasADi, Sympy, JAX, and PyCollimator generation."
    license = "Apache-2.0"
    homepage = "https://github.com/CogniPilot/rumoca"
    topics = ("modelica", "rust")
    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def build_requirements(self):
        self.tool_requires("rust/[^1.70.0]")

    def pacakge_id(self):
        del self.info.settings.compiler

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # Add a profile for RelWithDebInfo
        save(self, "Cargo.toml", content=textwrap.dedent("""\
            [profile.release-with-debug]
            inherits = "release"
            debug = true
        """), append=True)

    def generate(self):
        env = Environment()
        # Ensure the correct linker is used, especially when cross-compiling
        target_upper = self.conf.get("user.rust:target_host", check_type=str).upper().replace("-", "_")
        cc = GnuToolchain(self).extra_env.vars(self)["CC"]
        env.define_path(f"CARGO_TARGET_{target_upper}_LINKER", cc)
        # Don't add the Cargo dependencies to a global Cargo cache
        env.define_path("CARGO_HOME", os.path.join(self.build_folder, "cargo"))
        env.vars(self).save_script("cargo_paths")

    @property
    def _build_type_flag(self):
        if self.settings.build_type == "Debug":
            return ""
        elif self.settings.build_type == "RelWithDebInfo":
            return "--profile=release-with-debug"
        elif self.settings.build_type == "MinSizeRel":
            return "--profile=release-opt-size"
        return "--release"

    def build(self):
        self.run(f"cargo rustc -p rumoca --bin rumoca {self._build_type_flag} --target-dir {self.build_folder}", cwd=self.source_folder)

    @property
    def _dist_dir(self):
        build_type = "debug" if self.settings.build_type == "Debug" else "release"
        if cross_building(self):
            platform = self.conf.get("user.rust:target_host", check_type=str)
            return Path(self.build_folder, platform, build_type)
        return Path(self.build_folder, build_type)

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        suffix = ".exe" if self.settings.os == "Windows" else ""
        copy(self, f"rumoca{suffix}", self._dist_dir, os.path.join(self.package_folder, "bin"))

    def package_info(self):
        self.cpp_info.libdirs = []
        self.cpp_info.includedirs = []
