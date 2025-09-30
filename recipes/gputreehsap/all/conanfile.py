import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class GPUTreeShapConan(ConanFile):
    name = "gputreeshap"
    description = "GPUTreeShap is a CUDA implementation of the TreeShap algorithm by for Nvidia GPUs."
    license = "Apache-2.0"
    homepage = "https://github.com/rapidsai/gputreeshap"
    topics = ("gpu", "shap", "machine-learning", "cuda", "rapids", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type", "cuda"

    python_requires = "conan-cuda/latest"
    python_requires_extend = "conan-cuda.Cuda"

    def package_id(self):
        self.info.clear()

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.cuda.requires("cudart")

    def validate(self):
        check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # Add a missing include
        replace_in_file(self, "GPUTreeShap/gpu_treeshap.h",
                        "#include <thrust/host_vector.h>",
                        "#include <thrust/host_vector.h>\n"
                        "#include <thrust/sort.h>")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*.h", os.path.join(self.source_folder, "GPUTreeShap"),
             os.path.join(self.package_folder, "include", "GPUTreeShap"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "GPUTreeShap")
        self.cpp_info.set_property("cmake_target_name", "GPUTreeShap::GPUTreeShap")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
