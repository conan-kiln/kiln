import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cstd
from conan.tools.cmake import CMakeDeps, cmake_layout, CMake, CMakeToolchain
from conan.tools.files import *

required_conan_version = ">=2.1"


class SuperSCSConan(ConanFile):
    name = "superscs"
    description = "SuperSCS is is a fast and accurate solver for conic optimization problems"
    license = "MIT"
    homepage = "https://github.com/kul-optec/superscs"
    topics = ("optimization", "conic-programming", "convex-optimization", "solver")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "build_direct": [True, False],
        "build_indirect": [True, False],
        "float32": [True, False],
        "int32": [True, False],
        "with_openmp": [True, False],
        "with_cuda": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "build_direct": True,
        "build_indirect": True,
        "float32": False,
        "int32": False,
        "with_openmp": True,
        "with_cuda": False,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    python_requires = "conan-cuda/latest"

    @property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self)

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if not self.options.with_cuda:
            del self.settings.cuda

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("openblas/[>=0.3.0 <1]")
        if self.options.build_direct:
            self.requires("suitesparse-ldl/[^3.3]")
        if self.options.with_openmp:
            self.requires("openmp/system")
        if self.options.with_cuda:
            self.cuda.requires("cudart")
            self.cuda.requires("cublas")
            self.cuda.requires("cusparse")

    def validate(self):
        if self.settings.get_safe("compiler.cstd"):
            check_min_cstd(self, 99)
        if not self.options.build_direct and not self.options.build_indirect:
            raise ConanInvalidConfiguration("At least one of build_direct or build_indirect must be enabled")

    def build_requirements(self):
        if self.options.with_cuda:
            self.tool_requires(f"nvcc/[~{self.settings.cuda.version}]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        rmdir(self, "linsys/direct/external")
        replace_in_file(self, "linsys/direct/private.h", '#include "external/', '#include "')
        # Ensure the correct define value is used in public headers
        replace_in_file(self, "include/scs_blas.h", "#ifdef LAPACK_LIB_FOUND", "#if 1")
        replace_in_file(self, "include/cones.h", "#ifdef LAPACK_LIB_FOUND", "#if 1")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_DIRECT"] = self.options.build_direct
        tc.cache_variables["BUILD_INDIRECT"] = self.options.build_indirect
        tc.cache_variables["USE_OPENMP"] = self.options.with_openmp
        tc.cache_variables["FLOAT"] = self.options.float32
        tc.cache_variables["DLONG"] = not self.options.int32
        tc.cache_variables["BLAS64"] = self.dependencies["openblas"].options.interface == "ilp64"
        tc.cache_variables["GPU"] = self.options.with_cuda
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

        if self.options.with_cuda:
            cuda_tc = self.cuda.CudaToolchain()
            cuda_tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE*", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        rm(self, "*.pdb", self.package_folder, recursive=True)

    def package_info(self):
        if self.options.build_direct:
            self.cpp_info.components["scsdir"].set_property("cmake_target_name", "scsdir")
            self.cpp_info.components["scsdir"].set_property("pkg_config_name", "scsdir")
            self.cpp_info.components["scsdir"].libs = ["scsdir"]
            self.cpp_info.components["scsdir"].requires = ["suitesparse-ldl::suitesparse-ldl"]

        if self.options.build_indirect:
            self.cpp_info.components["scsindir"].set_property("cmake_target_name", "scsindir")
            self.cpp_info.components["scsindir"].set_property("pkg_config_name", "scsindir")
            self.cpp_info.components["scsindir"].libs = ["scsindir"]

        if self.options.with_cuda:
            self.cpp_info.components["scsgpu"].set_property("cmake_target_name", "scsgpu")
            self.cpp_info.components["scsgpu"].set_property("pkg_config_name", "scsgpu")
            self.cpp_info.components["scsgpu"].libs = ["scsgpu"]
            self.cpp_info.components["scsgpu"].requires = ["cudart::cudart_", "cublas::cublas_", "cusparse::cusparse"]

        for _, component in self.cpp_info.components.items():
            if self.settings.os in ["Linux", "FreeBSD"]:
                component.system_libs.extend(["m", "rt"])
            component.requires.append("openblas::openblas")
            if self.options.with_openmp:
                component.requires.append("openmp::openmp")
