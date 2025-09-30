import os
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class NvplLapackConan(ConanFile):
    name = "nvpl_lapack"
    description = ("NVPL LAPACK (NVIDIA Performance Libraries LAPACK) is part of NVIDIA Performance Libraries"
                   " that provides standard Fortran 90 LAPACK and LAPACKE APIs.")
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-Software-License-Agreement"
    homepage = "https://docs.nvidia.com/nvpl"
    topics = ("cuda", "nvpl", "lapack", "lapacke", "linear-algebra", "matrix-factorization")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "compatibility_headers": [True, False],
    }
    default_options = {
        "compatibility_headers": True,
    }

    python_requires = "conan-cuda/latest"

    @cached_property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self, enable_private=True)

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type

    def requirements(self):
        self.requires("nvpl_blas/[>=0.4 <1]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration("NVPL libraries are only supported on Linux")
        if self.settings.arch != "armv8":
            raise ConanInvalidConfiguration("NVPL libraries are only supported on armv8")

    def build(self):
        self.cuda.download_package("nvpl_lapack", platform_id="linux-sbsa")

    @property
    def _backend_name(self):
        blas_opts = self.dependencies["nvpl_blas"].options
        name = f"nvpl_lapack_{blas_opts.interface}"
        if blas_opts.threading == "omp":
            name += "_gomp"
        else:
            name += "_seq"
        return name

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        copy(self, "libnvpl_lapack_core.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
        copy(self, f"lib{self._backend_name}.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
        if self.options.compatibility_headers:
            save(self, os.path.join(self.package_folder, "include", "lapack.h"), '#include "nvpl_lapack.h"\n')
            save(self, os.path.join(self.package_folder, "include", "lapacke.h"), '#include "nvpl_lapacke.h"\n')

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "nvpl_lapack")

        def _add_component(name):
            component = self.cpp_info.components[name]
            component.set_property("cmake_target_name", name)
            component.set_property("cmake_target_aliases", [name.replace("nvpl_", "nvpl::")])
            component.libs = [name]
            if "ilp64" in name:
                component.defines = ["NVPL_ILP64"]
            component.requires = [f"nvpl_blas::{name.replace('lapack', 'blas')}"]
            if name != "nvpl_lapack_core":
                component.requires.append("nvpl_lapack_core")

        _add_component("nvpl_lapack_core")
        _add_component(self._backend_name)
