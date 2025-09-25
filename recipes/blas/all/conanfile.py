import os
import textwrap
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.files import *

required_conan_version = ">=2.1"


class BlasConan(ConanFile):
    name = "blas"
    version = "latest"
    description = "BLAS (Basic Linear Algebra Subprograms) meta-package for Conan"
    license = "MIT"
    homepage = "https://www.netlib.org/blas/"
    topics = ("blas", "linear-algebra", "meta-package")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "provider": [
            "openblas",
            "mkl",
            "blis",
            "accelerate",
            "armpl",
            "nvpl",
            # TODO:
            # libblastrampoline
            # flexiblas
        ],
        "interface": ["lp64", "ilp64"],
    }
    default_options = {
        "shared": False,
        "provider": "openblas",
        "interface": "lp64",
    }

    @cached_property
    def _dep_name(self):
        provider = str(self.options.provider)
        return {
            "mkl": "onemkl",
            "nvpl": "nvpl_blas",
        }.get(provider, provider)

    def configure(self):
        self.options[self._dep_name].interface = self.options.interface
        if self.options.provider in ["mkl", "nvpl", "accelerate"]:
            self.options.shared.value = True
        else:
            self.options[self._dep_name].shared = self.options.shared

    def requirements(self):
        if self.options.provider == "openblas":
            self.requires("openblas/[>=0.3 <1]")
        elif self.options.provider == "mkl":
            self.requires("onemkl/[*]")
        elif self.options.provider == "blis":
            self.requires("blis/[^2.0]")
        elif self.options.provider == "armpl":
            self.requires("armpl/[*]")
        elif self.options.provider == "nvpl":
            self.requires("nvpl_blas/[<1]")

    def package_id(self):
        self.info.clear()

    @cached_property
    def _dependency(self):
        return self.dependencies[self._dep_name]

    def validate(self):
        if self.options.provider == "accelerate" and not is_apple_os(self):
            raise ConanInvalidConfiguration("Accelerate provider is only available on Apple OS-s")
        if self._dependency.options.interface != self.options.interface:
            raise ConanInvalidConfiguration(f"-o {self._dependency.ref}:interface != {self.options.interface} value from -o {self.ref}:interface")
        if self.options.provider not in ["mkl", "nvpl", "accelerate"]:
            if self._dependency.options.shared != self.options.shared:
                raise ConanInvalidConfiguration(f"-o {self._dependency.ref}:shared != {self.options.shared} value from -o {self.ref}:shared")

    def package(self):
        bla_vendor = {
            "openblas": "OpenBLAS",
            "mkl": "Intel10",
            "blis": "FLAME",
            "accelerate": "Apple",
            "armpl": "Arm",
            "nvpl": "NVPL",
            "libblastrampoline": "libblastrampoline",
            "flexiblas": "FlexiBLAS",
        }[str(self.options.provider)]
        save(self, os.path.join(self.package_folder, "share", "conan", "blas-wrapper.cmake"), textwrap.dedent(f"""\
            set(CONAN_BLA_VENDOR {bla_vendor})
        """))

    def package_info(self):
        self.cpp_info.set_property("cmake_find_mode", "both")
        self.cpp_info.set_property("cmake_file_name", "BLAS")
        self.cpp_info.set_property("cmake_target_name", "BLAS::BLAS")
        self.cpp_info.set_property("pkg_config_name", "blas")

        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.includedirs = []

        if self.options.provider == "accelerate":
            self.cpp_info.frameworks = ["Accelerate"]

        self.cpp_info.builddirs = ["share/conan"]
        self.cpp_info.set_property("cmake_build_modules", ["share/conan/blas-wrapper.cmake"])
