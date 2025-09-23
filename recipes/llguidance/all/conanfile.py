import os
import shutil
import textwrap
from functools import cached_property
from pathlib import Path

from conan import ConanFile
from conan.tools.build import cross_building
from conan.tools.env import Environment
from conan.tools.files import *
from conan.tools.gnu import GnuToolchain
from conan.tools.layout import basic_layout

required_conan_version = ">=2.4"


class LLGuidanceConan(ConanFile):
    name = "llguidance"
    description = "Super-fast Structured Outputs for Large Language Models"
    license = "MIT"
    homepage = "https://github.com/guidance-ai/llguidance"
    topics = ("llm", "structured-output", "constrained-decoding", "grammar", "json-schema")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "lark": [True, False],
        "jsonschema_validation": [True, False],
        "rayon": [True, False],
        "referencing": [True, False],
        "ahash": [True, False],
    }
    default_options = {
        "shared": False,
        "lark": True,
        "jsonschema_validation": False,
        "rayon": True,
        "referencing": True,
        "ahash": True,
    }
    languages = ["C"]

    def layout(self):
        basic_layout(self, src_folder="src")

    def build_requirements(self):
        self.tool_requires("rust/[>=1.75]")

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

    @cached_property
    def _cargo_features(self):
        features = []
        if self.options.lark:
            features.append("lark")
        if self.options.jsonschema_validation:
            features.append("jsonschema_validation")
        if self.options.rayon:
            features.append("rayon")
        if self.options.referencing:
            features.append("referencing")
        if self.options.ahash:
            features.append("ahash")
        return features

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

    @property
    def _features_flag(self):
        if self._cargo_features:
            return f"--features={','.join(self._cargo_features)}"
        return "--no-default-features"

    def build(self):
        self.run(f"cargo rustc -p llguidance {self._build_type_flag} {self._shared_flag} {self._features_flag} --target-dir {self.build_folder}",
                 cwd=self.source_folder)

    @property
    def _dist_dir(self):
        build_type = "debug" if self.settings.build_type == "Debug" else "release"
        if cross_building(self):
            platform = self.conf.get("user.rust:target_host", check_type=str)
            return Path(self.build_folder, platform, build_type)
        return Path(self.build_folder, build_type)

    def package(self):
        copy(self, "LICENSE*", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "llguidance.h", os.path.join(self.source_folder, "parser"), os.path.join(self.package_folder, "include"))
        # Using shutil since copy() copies unrelated junk
        for path in self._dist_dir.glob("*llguidance.*"):
            if path.suffix == ".d" or path.suffix == ".h":
                continue
            dest = Path(self.package_folder, "bin" if path.suffix == ".dll" else "lib")
            dest.mkdir(exist_ok=True)
            shutil.copy2(path, os.path.join(dest, path.name))

    def package_info(self):
        self.cpp_info.libs = ["llguidance"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]
