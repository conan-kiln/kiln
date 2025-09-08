import os
from functools import cached_property

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class CuSolverConan(ConanFile):
    name = "cusolver"
    description = "cuSOLVER: a GPU-accelerated LAPACK-like library on dense and sparse linear algebra"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-CUDA-Toolkit-EULA"
    homepage = "https://docs.nvidia.com/cuda/cusolver/"
    topics = ("cuda", "linear-algebra", "solver", "matrix", "decomposition", "lapack")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "cmake_alias": [True, False],
        "use_stubs": [True, False],
        "cusolverMg": [True, False],
    }
    default_options = {
        "shared": False,
        "cmake_alias": True,
        "use_stubs": False,
        "cusolverMg": False,
    }

    python_requires = "conan-cuda/latest"

    @cached_property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self, enable_private=True)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.shared
            del self.options.use_stubs
            self.package_type = "shared-library"

    def configure(self):
        if not self.options.get_safe("shared", True):
            self.options.rm_safe("use_stubs")
            del self.options.cusolverMg

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        del self.info.settings.cuda.architectures
        self.info.settings.cuda.version = self.cuda.major
        self.info.settings.rm_safe("cmake_alias")
        self.info.settings.rm_safe("use_stubs")

    def requirements(self):
        self.cuda.requires("cudart", transitive_headers=True, transitive_libs=True)
        self.cuda.requires("cublas", transitive_headers=True, transitive_libs=True)
        self.cuda.requires("cusparse", transitive_headers=True, transitive_libs=True)
        if self.settings.os == "Linux" and not self.options.shared:
            self.cuda.requires("culibos")

    def validate(self):
        self.cuda.validate_package("libcusolver")
        if self.options.get_safe("shared", True):
            self.cuda.require_shared_deps(["cublas", "cusparse"])
        self.cuda.require_shared_deps(["rdma-core"])

    def build(self):
        self.cuda.download_package("libcusolver")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        if self.settings.os == "Linux":
            if self.options.shared:
                copy(self, "libcusolver.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
                if self.options.cusolverMg:
                    copy(self, "libcusolverMg.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
                copy(self, "*.so*", os.path.join(self.source_folder, "lib", "stubs"), os.path.join(self.package_folder, "lib", "stubs"))
            else:
                copy(self, "*_static.a", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
        else:
            bin_dir = os.path.join(self.source_folder, "bin", "x64") if self.cuda.major >= 13 else os.path.join(self.source_folder, "bin")
            lib_dir = os.path.join(self.source_folder, "lib", "x64")
            copy(self, "cusolver*.dll", bin_dir, os.path.join(self.package_folder, "bin"))
            copy(self, "cusolver.lib", lib_dir, os.path.join(self.package_folder, "lib"))
            if self.options.cusolverMg:
                copy(self, "cusolverMg*.dll", bin_dir, os.path.join(self.package_folder, "bin"))
                copy(self, "cusolverMg.lib", lib_dir, os.path.join(self.package_folder, "lib"))

    def package_info(self):
        suffix = "" if self.options.get_safe("shared", True) else "_static"
        self.cpp_info.components["cusolver_"].set_property("pkg_config_name", f"cusolver-{self.cuda.version}")
        self.cpp_info.components["cusolver_"].set_property("pkg_config_aliases", ["cusolver"])  # unofficial
        self.cpp_info.components["cusolver_"].set_property("component_version", str(self.cuda.version))
        self.cpp_info.components["cusolver_"].set_property("cmake_target_name", f"CUDA::cusolver{suffix}")
        if self.options.get_safe("cmake_alias"):
            alias_suffix = "_static" if self.options.get_safe("shared", True) else ""
            self.cpp_info.components["cusolver_"].set_property("cmake_target_aliases", [f"CUDA::cusolver{alias_suffix}"])
        self.cpp_info.components["cusolver_"].libs = [f"cusolver{suffix}"]
        if self.options.get_safe("use_stubs"):
            self.cpp_info.components["cusolver_"].libdirs = ["lib/stubs", "lib"]
        self.cpp_info.components["cusolver_"].requires = ["cudart::cudart_", "cublas::cublas_", "cusparse::cusparse"]
        if self.settings.os == "Linux" and not self.options.shared:
            self.cpp_info.components["cusolver_"].system_libs = ["rt", "pthread", "m", "dl", "gcc_s", "stdc++"]
            self.cpp_info.components["cusolver_"].requires.append("culibos::culibos")

        if self.options.get_safe("cusolverMg"):
            self.cpp_info.components["cusolverMg"].set_property("cmake_target_name", "CUDA::cusolverMg")
            self.cpp_info.components["cusolverMg"].libs = ["cusolverMg"]
            if self.options.get_safe("use_stubs"):
                self.cpp_info.components["cusolverMg"].libdirs = ["lib/stubs", "lib"]
            self.cpp_info.components["cusolverMg"].requires = ["cudart::cudart_", "cublas::cublas_"]

        # internal components
        if not self.options.get_safe("shared", True):
            if Version(self.version) >= "11.3":
                self.cpp_info.components["cusolver_lapack"].libs = ["cusolver_lapack_static"]
                self.cpp_info.components["cusolver_"].requires.append("cusolver_lapack")
            else:
                self.cpp_info.components["lapack"].libs = ["lapack_static"]
                self.cpp_info.components["cusolver_"].requires.append("lapack")
            self.cpp_info.components["metis"].libs = ["metis_static"]
            if Version(self.version) >= "11.4":
                self.cpp_info.components["cusolver_metis"].libs = ["cusolver_metis_static"]
                self.cpp_info.components["cusolver_metis"].requires = ["metis"]
                self.cpp_info.components["cusolver_"].requires.append("cusolver_metis")
            else:
                self.cpp_info.components["cusolver_"].requires.append("metis")
