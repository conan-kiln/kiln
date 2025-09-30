import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class ScalapackConan(ConanFile):
    name = "scalapack"
    description = "Scalable Linear Algebra PACKage"
    license = "BSD-3-Clause"
    homepage = "http://www.netlib.org/scalapack/"
    topics = ("linear-algebra", "distributed-computing", "mpi", "lapack", "blas")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    @property
    def _fortran_compiler(self):
        executables = self.conf.get("tools.build:compiler_executables", default={}, check_type=dict)
        return executables.get("fortran")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("lapack/latest", transitive_headers=True)
        self.requires("openmpi/[>=4 <6]", transitive_headers=True, transitive_libs=True)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.26 <5]")

    def validate_build(self):
        if not self._fortran_compiler:
            raise ConanInvalidConfiguration(
                "A Fortran compiler is required. "
                "Please add one to `tools.build:compiler_executables={'fortran': '...'}`."
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # Require MPI
        replace_in_file(self, "CMakeLists.txt", "find_package(MPI)", "find_package(MPI REQUIRED)")
        # Don't bother with the xintface executable for name mangling detection, which is not cross-compilation compatible
        save(self, "BLACS/INSTALL/CMakeLists.txt", "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["SCALAPACK_BUILD_TESTS"] = False
        tc.cache_variables["BUILD_TESTING"] = False
        tc.cache_variables["USE_OPTIMIZED_LAPACK_BLAS"] = True
        tc.cache_variables["CDEFS"] = "Add_"  # Fortran name mangling
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "scalapack")
        self.cpp_info.set_property("cmake_target_aliases", ["scalapack"])
        self.cpp_info.set_property("pkg_config_name", "scalapack")
        # For compatibility with Debian
        self.cpp_info.set_property("pkg_config_aliases", ["scalapack-openmpi"])
        self.cpp_info.libs = ["scalapack"]
        # ScaLAPACK does not provide any C headers
        self.cpp_info.includedirs = []
        if not self.options.shared:
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.system_libs = ["m", "dl"]
            if "gfortran" in self._fortran_compiler:
                self.cpp_info.system_libs.append("gfortran")
        self.cpp_info.requires = ["lapack::lapack", "openmpi::ompi-c"]
