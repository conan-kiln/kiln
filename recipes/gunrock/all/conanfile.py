import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class GunrockConan(ConanFile):
    name = "gunrock"
    description = "CUDA/C++ GPU Graph Analytics library with high-level, bulk-synchronous, data-centric abstraction"
    license = "Apache-2.0"
    homepage = "https://github.com/gunrock/gunrock"
    topics = ("graph", "graph-algorithms", "hpc", "gpu", "parallel-computing", "cuda", "graph-processing",
              "graph-analytics", "sparse-matrix", "graph-engine", "graph-primitives", "graph-neural-networks", "gnn", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    implements = ["auto_shared_fpic"]

    python_requires = "conan-cuda/latest"
    python_requires_extend = "conan-cuda.Cuda"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("cxxopts/[^3.0]")
        self.requires("nlohmann_json/[^3.0]")
        self.requires("moderngpu/[^2]")
        self.cuda.requires("cudart")

    def validate(self):
        check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))

    @property
    def _supported_sms(self):
        # https://github.com/gunrock/gunrock/blob/530f25443864d04c25286c053d6812a888b4d779/include/gunrock/cuda/sm.hxx#L24-L38
        return [30, 35, 37, 50, 52, 53, 60, 61, 62, 70, 72, 75, 80, 86, 90]

    @property
    def _minimum_sm(self):
        architectures = [x.split("-")[0] for x in str(self.settings.cuda.architectures).split(",")]
        min_arch = min(int(x) for x in architectures if x.isnumeric())
        return max(x for x in self._supported_sms if x < min_arch)

    def package_info(self):
        self.cpp_info.libdirs = []
        self.cpp_info.bindirs = []
        self.cpp_info.defines = [f"ESSENTIALS_VERSION={self.version}"]
        self.cpp_info.defines.append(f"SM_TARGET={self._minimum_sm}")
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["pthread", "dl"]
