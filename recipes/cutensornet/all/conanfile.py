import os
from functools import cached_property

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class CuTensorNetConan(ConanFile):
    name = "cutensornet"
    description = "cuTensorNet: A High-Performance Library for Tensor Network Computations"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-Software-License-Agreement"
    homepage = "https://docs.nvidia.com/cuda/cuquantum/latest/cutensornet/index.html"
    topics = ("cuda", "tensor", "tensor-networks", "linear-algebra", "deep-learning", "nvidia")
    # static is also supported but requires an additional ExaTN dependency
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type", "cuda"

    python_requires = "conan-cuda/latest"

    @cached_property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self, enable_private=True)

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        del self.info.settings.cuda.architectures
        self.info.settings.cuda.version = self.cuda.major
        self.info.settings.rm_safe("cmake_alias")

    def requirements(self):
        self.cuda.requires("cudart", transitive_headers=True, transitive_libs=True)
        self.cuda.requires("cublas")
        self.cuda.requires("cusolver")
        self.cuda.requires("cutensor")

    def validate(self):
        self.cuda.validate_package("cuquantum", ignore_version=True)
        if self.options.get_safe("shared", True):
            self.cuda.require_shared_deps(["cutensor", "cusolver", "cublas"])

    def build(self):
        self.cuda.download_package("cuquantum", ignore_version=True)

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        rm(self, "cudensitymat*", os.path.join(self.package_folder, "include"))
        rm(self, "custatevec*", os.path.join(self.package_folder, "include"))
        def copy_lib(lib):
            if self.options.get_safe("shared", True):
                copy(self, f"*{lib}.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
            else:
                copy(self, f"*{lib}_static.a", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
        copy_lib("cutensornet")

    def package_info(self):
        # The CMake config and target names are not official
        self.cpp_info.set_property("cmake_file_name", "cuTensorNet")
        self.cpp_info.set_property("cmake_target_name", "cuTensorNet::cuTensorNet")
        self.cpp_info.set_property("cmake_target_aliases", [f"cuTensorNet::cutensornet", f"cuTensorNet::cutensornet_static"])
        self.cpp_info.set_property("pkg_config_name", "cutensornet")  # unofficial
        suffix = "" if self.options.get_safe("shared", True) else "_static"
        self.cpp_info.libs = [f"cutensornet{suffix}"]
        self.cpp_info.requires = [
            "cudart::cudart_",
            "cublas::cublas_",
            "cutensor::cutensor_",
            "cusolver::cusolver_",
        ]
        if not self.options.get_safe("shared", True):
            self.cpp_info.system_libs = ["m", "pthread", "dl", "rt", "stdc++", "gcc_s"]
