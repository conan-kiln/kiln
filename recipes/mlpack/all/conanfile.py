import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc

required_conan_version = ">=2.1"


class MlpackConan(ConanFile):
    name = "mlpack"
    description = "mlpack: a fast, header-only C++ machine learning library"
    license = "BSD-3-Clause"
    homepage = "https://github.com/mlpack/mlpack"
    topics = ("machine-learning", "deep-learning", "regression", "nearest-neighbor-search", "scientific-computing", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("armadillo/[<14]")
        self.requires("ensmallen/[^2.21.0]")
        self.requires("cereal/[^1.3.2]")
        self.requires("stb/[*]")
        # https://github.com/mlpack/mlpack/blob/4.4.0/src/mlpack/methods/det/dt_utils_impl.hpp#L184
        self.requires("openmp/system", transitive_headers=True, transitive_libs=True)

    def package_id(self):
        self.info.clear()

    def validate(self):
        check_min_cppstd(self, 17)
        if not self.dependencies["armadillo"].options.with_blas or not self.dependencies["armadillo"].options.with_lapack:
            raise ConanInvalidConfiguration("mlpack requires armadillo to be built with BLAS and LAPACK support.")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*",
             os.path.join(self.source_folder, "src"),
             os.path.join(self.package_folder, "include"),
             excludes=["mlpack/bindings/*", "mlpack/tests/*", "mlpack/CMakeLists.txt"])

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "mlpack")
        self.cpp_info.set_property("cmake_target_name", "mlpack::mlpack")
        self.cpp_info.set_property("pkg_config_name", "mlpack")

        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []

        self.cpp_info.defines.append("MLPACK_USE_SYSTEM_STB")

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.extend(["m", "pthread"])

        if self.settings.get_safe("compiler.libcxx") in ["libstdc++", "libstdc++11"]:
            self.cpp_info.system_libs.append("atomic")

        flags = []
        if self.settings.compiler == "gcc" and self.settings.os == "Windows":
            flags = ["-Wa,-mbig-obj"]
        elif is_msvc(self):
            # https://github.com/mlpack/mlpack/blob/4.3.0/CMakeLists.txt#L164-L175
            flags = ["/bigobj", "/Zm200", "/Zc:__cplusplus"]
        if flags:
            self.cpp_info.cflags = flags
            self.cpp_info.cxxflags = flags
