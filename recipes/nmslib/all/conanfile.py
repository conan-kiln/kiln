import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration, ConanException
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout, CMakeDeps
from conan.tools.files import *
from conan.tools.microsoft import is_msvc, check_min_vs
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class Nmslib(ConanFile):
    name = "nmslib"
    description = (
        "Non-Metric Space Library (NMSLIB): An efficient similarity search library "
        "and a toolkit for evaluation of k-NN methods for generic non-metric spaces."
    )
    license = "Apache-2.0"
    homepage = "https://github.com/nmslib/nmslib"
    topics = ("knn-search", "non-metric", "neighborhood-graphs", "neighborhood-graphs", "vp-tree")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "build_extras": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "build_extras": True,
    }
    options_description = {
        "build_extras": "Add support for Signature Quadratic Form Distance (SQFD). Not supported on MSVC.",
    }
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if is_msvc(self):
            # Not available on MSVC
            # https://github.com/nmslib/nmslib/blob/v2.1.1/similarity_search/include/space/space_sqfd.h#L19
            del self.options.build_extras
            del self.options.shared
            self.package_type = "static-library"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.get_safe("build_extras"):
            self.requires("eigen/[>=3.3 <6]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        # The finite-math-only optimization has no effect and can cause linking errors
        # when linked against glibc >= 2.31
        replace_in_file(self, "similarity_search/CMakeLists.txt", "-Ofast", "-Ofast -fno-finite-math-only")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["WITH_EXTRAS"] = self.options.get_safe("build_extras", False)
        tc.variables["WITHOUT_TESTS"] = True
        # Relocatable shared libs on macOS
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0042"] = "NEW"
        tc.cache_variables["CMAKE_POLICY_VERSION_MINIMUM"] = "3.5" # CMake 4 support
        if Version(self.version) > "2.1.1":
            raise ConanException("CMAKE_POLICY_VERSION_MINIMUM hardcoded to 3.5, check if new version supports CMake 4")
        tc.generate()
        deps = CMakeDeps(self)
        deps.set_property("eigen", "cmake_file_name", "EIGEN")
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder="similarity_search")
        cmake.build()

    def package(self):
        copy(self, "LICENSE",
             dst=os.path.join(self.package_folder, "licenses"),
             src=self.source_folder)
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["NonMetricSpaceLib"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["pthread", "m"]
            if self.settings.arch in ["x86", "x86_64"]:
                self.cpp_info.system_libs.append("mvec")
        if self.options.get_safe("build_extras"):
            self.cpp_info.defines.append("WITH_EXTRAS")
