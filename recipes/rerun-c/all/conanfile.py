import os
import shutil
import textwrap
from pathlib import Path

from conan import ConanFile
from conan.tools.apple import is_apple_os
from conan.tools.build import cross_building
from conan.tools.env import Environment
from conan.tools.files import *
from conan.tools.gnu import AutotoolsToolchain
from conan.tools.layout import basic_layout

required_conan_version = ">=2.4"


class RerunCConan(ConanFile):
    name = "rerun-c"
    description = "Rerun C SDK for multimodal data visualization"
    license = "MIT OR Apache-2.0"
    homepage = "https://github.com/rerun-io/rerun"
    topics = ("visualization", "logging", "multimodal", "3d", "computer-vision")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
    }
    default_options = {
        "shared": False,
    }
    languages = ["C"]

    def layout(self):
        basic_layout(self, src_folder="src")

    def build_requirements(self):
        self.tool_requires("rust/[^1.88]")

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
        cc = AutotoolsToolchain(self).vars().get("CC")
        if cc:
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

    @property
    def _shared_flag(self):
        return "--crate-type=cdylib" if self.options.shared else "--crate-type=staticlib"

    def build(self):
        self.run(f"cargo rustc -p rerun_c {self._build_type_flag} {self._shared_flag} --target-dir {self.build_folder}",
                 cwd=self.source_folder)

    @property
    def _dist_dir(self):
        build_type = "debug" if self.settings.build_type == "Debug" else "release"
        if cross_building(self):
            platform = self.conf.get("user.rust:target_host", check_type=str)
            return Path(self.build_folder, platform, build_type)
        return Path(self.build_folder, build_type)

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "rerun_cpp/src/rerun/c"), os.path.join(self.package_folder, "include/rerun/c"))
        for path in self._dist_dir.glob("*rerun_c.*"):
            if path.suffix == ".d":
                continue
            dest = Path(self.package_folder, "bin" if path.suffix == ".dll" else "lib")
            dest.mkdir(exist_ok=True)
            shutil.copy2(path, os.path.join(dest, path.name))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "rerun_c")
        self.cpp_info.set_property("cmake_target_name", "rerun_c")
        self.cpp_info.set_property("nosoname", True)
        self.cpp_info.libs = ["rerun_c"]
        self.cpp_info.includedirs = ["include", "include/rerun"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m", "dl", "pthread"]
        elif is_apple_os(self):
            self.cpp_info.frameworks = ["CoreFoundation", "IOKit", "Security"]
        elif self.settings.os == "Windows":
            self.cpp_info.system_libs = [
                "Crypt32", "Iphlpapi", "Ncrypt", "Netapi32", "ntdll",
                "Pdh", "PowrProf", "Psapi", "Secur32", "Userenv", "ws2_32"
            ]
