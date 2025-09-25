from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration

required_conan_version = ">=2.1"


class LapackConan(ConanFile):
    name = "lapack"
    version = "latest"
    description = "LAPACK meta-package for Conan"
    license = "MIT"
    homepage = "https://www.netlib.org/lapack/"
    topics = ("blas", "linear-algebra", "meta-package")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "provider": [
            "reference",
            "openblas",
            "mkl",
            "accelerate",
            "armpl",
            "nvpl",
            # TODO:
            # libblastrampoline
            # flexiblas
        ],
    }
    default_options = {
        "provider": "openblas",
    }

    def configure(self):
        if self.options.provider != "reference":
            self.options["blas"].provider = self.options.provider
        self.options["openblas"].build_lapack = self.options.provider == "openblas"

    def requirements(self):
        self.requires("blas/latest")
        if self.options.provider == "reference":
            self.requires("lapack-reference/[^3.12]")
        elif self.options.provider == "nvpl":
            self.requires("nvpl_lapack/[<1]")

    def package_id(self):
        self.info.clear()

    @cached_property
    def _dependency(self):
        return self.dependencies[self._dep_name]

    def validate(self):
        if self.options.provider != "reference":
            if self.dependencies["blas"].options.provider != self.options.provider:
                raise ConanInvalidConfiguration(
                    "-o blas/latest:provider and -o lapack/latest:provider must match "
                    f"({self.dependencies['blas'].options.provider} != {self.options.provider})")
        if self.options.provider == "openblas" and not self.dependencies["openblas"].options.build_lapack:
            raise ConanInvalidConfiguration("-o openblas/*:build_lapack must be enabled")

    def package_info(self):
        self.cpp_info.set_property("cmake_find_mode", "both")
        self.cpp_info.set_property("cmake_file_name", "LAPACK")
        self.cpp_info.set_property("cmake_target_name", "LAPACK::LAPACK")
        if self.options.provider != "reference":
            self.cpp_info.set_property("pkg_config_name", "lapack")

        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.includedirs = []
