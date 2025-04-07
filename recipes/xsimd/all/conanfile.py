from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import copy, get
from conan.tools.layout import basic_layout
from conan.tools.scm import Version
from conan.tools.apple import is_apple_os
from conan.tools.build import check_min_cppstd
import os

required_conan_version = ">=2.1"


class XsimdConan(ConanFile):
    name = "xsimd"
    description = "C++ wrappers for SIMD intrinsics and parallelized, optimized mathematical functions (SSE, AVX, NEON, AVX512)"
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/xtensor-stack/xsimd"
    topics = ("simd-intrinsics", "vectorization", "simd", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "xtl_complex": [True, False],
    }
    default_options = {
        "xtl_complex": False,
    }
    no_copy_source = True

    @property
    def _min_cppstd(self):
        return 14 if self.options.xtl_complex else 11

    @property
    def _compilers_minimum_version(self):
        return {
            "14": {
                "gcc": "6",
                "clang": "5",
                "apple-clang": "10",
                "msvc": "191",
            },
        }.get(self._min_cppstd, {})

    def requirements(self):
        if self.options.xtl_complex:
            self.requires("xtl/0.7.5")

    def package_id(self):
        self.info.clear()

    def validate(self):
        # TODO: check supported version (probably >= 8.0.0)
        if Version(self.version) < "8.0.0" and is_apple_os(self) and self.settings.arch in ["armv8", "armv8_32", "armv8.3"]:
            raise ConanInvalidConfiguration(f"{self.ref} doesn't support macOS M1")

        check_min_cppstd(self, self._min_cppstd)
        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if minimum_version and Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(
                f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support."
            )

    def layout(self):
        basic_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        includedir = os.path.join(self.source_folder, "include")
        copy(self, "*.hpp", src=includedir, dst=os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "xsimd")
        self.cpp_info.set_property("cmake_target_name", "xsimd")
        self.cpp_info.set_property("pkg_config_name", "xsimd")
        if self.options.xtl_complex:
            self.cpp_info.defines = ["XSIMD_ENABLE_XTL_COMPLEX=1"]
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []

        ## TODO: workaround for arm compilation issue : https://github.com/xtensor-stack/xsimd/issues/735
        if Version(self.version) >= "9.0.0" and \
            is_apple_os(self) and self.settings.arch in ["armv8", "armv8_32", "armv8.3"]:
            self.cpp_info.cxxflags.extend(["-flax-vector-conversions", "-fsigned-char",])
