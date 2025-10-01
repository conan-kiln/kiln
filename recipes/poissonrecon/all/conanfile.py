import os

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class PoissonReconConan(ConanFile):
    name = "poissonrecon"
    description = "Headers for PoissonRecon: Adaptive Multigrid Solvers"
    license = "MIT"
    homepage = "https://github.com/mkazhdan/PoissonRecon"
    topics = ("surface-reconstruction", "multigrid-solver", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def package(self):
        copy(self, "LICENSE*", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "Src"), os.path.join(self.package_folder, "include", "PoissonRecon"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
