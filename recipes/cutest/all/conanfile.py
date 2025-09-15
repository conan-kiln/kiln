import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.meson import Meson, MesonToolchain
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class CutestConan(ConanFile):
    name = "cutest"
    description = "Constrained and Unconstrained Testing Environment with safe threads for optimization software"
    license = "BSD-3-Clause"
    homepage = "https://github.com/ralna/CUTEst"
    topics = ("optimization", "testing", "constrained-optimization", "unconstrained-optimization")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "quadruple": [True, False],
        "int64": [True, False],
    }
    default_options = {
        "quadruple": True,
        "int64": False,
    }
    languages = ["C"]

    @property
    def _fortran_compiler(self):
        executables = self.conf.get("tools.build:compiler_executables", default={}, check_type=dict)
        return executables.get("fortran")

    def layout(self):
        basic_layout(self, src_folder="src")

    def validate_build(self):
        if not self._fortran_compiler:
            raise ConanInvalidConfiguration(
                f"{self.name} requires a Fortran compiler. "
                "Please provide one by setting tools.build:compiler_executables={'fortran': '...'}."
            )

    def validate(self):
        if self.options.quadruple:
            if "arm" in str(self.settings.arch):
                raise ConanInvalidConfiguration("quadruple=True is not supported on ARM architectures")

    def build_requirements(self):
        self.tool_requires("meson/[>=0.62.0]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = MesonToolchain(self)
        tc.project_options["tests"] = False
        tc.project_options["quadruple"] = self.options.quadruple
        tc.project_options["int64"] = self.options.int64
        tc.project_options["modules"] = False
        tc.project_options["default_library"] = "shared"
        tc.generate()
        replace_in_file(self, "conan_meson_native.ini", "[binaries]", f"[binaries]\nfc = '{self._fortran_compiler}'")

    def build(self):
        meson = Meson(self)
        meson.configure()
        meson.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        meson = Meson(self)
        meson.install()

    def package_info(self):
        suffix = "_64" if self.options.int64 else ""
        self.cpp_info.components["single"].libs = ["cutest_single" + suffix]
        self.cpp_info.components["double"].libs = ["cutest_double" + suffix]
        if self.options.quadruple:
            self.cpp_info.components["quadruple"].libs = ["cutest_quadruple" + suffix]
