import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMakeToolchain, CMakeDeps, CMake
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class TinyExrConan(ConanFile):
    name = "tinyexr"
    description = "Tiny OpenEXR image loader/saver library"
    license = "BSD-3-Clause"
    homepage = "https://github.com/syoyo/tinyexr"
    topics = ("exr", "header-only")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "header_only": [True, False],
        "shared": [True, False],
        "fPIC": [True, False],
        "with_z": ["zlib", "miniz"],
        "with_piz": [True, False],
        "with_zfp": [True, False],
        "with_thread": [True, False],
        "with_openmp": [True, False],
    }
    default_options = {
        "header_only": True,
        "shared": False,
        "fPIC": True,
        "with_z": "miniz",
        "with_piz": True,
        "with_zfp": False,
        "with_thread": False,
        "with_openmp": True,
    }
    implements = ["auto_header_only", "auto_shared_fpic"]

    exports_sources = "CMakeLists.txt"

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_z == "miniz":
            self.requires("miniz/[^3.0.2]", transitive_headers=True, transitive_libs=True)
        else:
            self.requires("zlib-ng/[^2.0]", transitive_headers=True, transitive_libs=True)
        if self.options.with_zfp:
            self.requires("zfp/[^1.0.1]", transitive_headers=True, transitive_libs=True)
        if self.options.with_openmp:
            self.requires("openmp/system", transitive_headers=True, transitive_libs=True)

    def validate(self):
        if self.options.with_thread:
            check_min_cppstd(self, "11")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        if not self.options.header_only:
            tc = CMakeToolchain(self)
            tc.cache_variables["USE_MINIZ"] = self.options.with_z == "miniz"
            tc.cache_variables["USE_ZLIB"] = self.options.with_z == "zlib"
            tc.cache_variables["USE_PIZ"] = self.options.with_piz
            tc.cache_variables["USE_ZFP"] = self.options.with_zfp
            tc.cache_variables["USE_THREAD"] = self.options.with_thread
            tc.cache_variables["USE_OPENMP"] = self.options.with_openmp
            tc.generate()
            deps = CMakeDeps(self)
            deps.generate()

    def build(self):
        if not self.options.header_only:
            cmake = CMake(self)
            cmake.configure(build_script_folder="..")
            cmake.build()

    @property
    def _extracted_license(self):
        content_lines = open(os.path.join(self.source_folder, "tinyexr.h")).readlines()
        license_content = []
        for i in range(3, 27):
            license_content.append(content_lines[i][:-1])
        return "\n".join(license_content)

    def package(self):
        save(self, os.path.join(self.package_folder, "licenses", "LICENSE"), self._extracted_license)
        if self.options.header_only:
            copy(self, "tinyexr.h", self.source_folder, os.path.join(self.package_folder, "include"))
        else:
            cmake = CMake(self)
            cmake.install()

    def package_info(self):
        if self.options.header_only:
            self.cpp_info.bindirs = []
            self.cpp_info.libdirs = []
        else:
            self.cpp_info.libs = ["tinyexr"]
        self.cpp_info.defines.append("TINYEXR_USE_MINIZ={}".format("1" if self.options.with_z == "miniz" else "0"))
        self.cpp_info.defines.append("TINYEXR_USE_PIZ={}".format("1" if self.options.with_piz else "0"))
        self.cpp_info.defines.append("TINYEXR_USE_ZFP={}".format("1" if self.options.with_zfp else "0"))
        self.cpp_info.defines.append("TINYEXR_USE_THREAD={}".format("1" if self.options.with_thread else "0"))
        self.cpp_info.defines.append("TINYEXR_USE_OPENMP={}".format("1" if self.options.with_openmp else "0"))

        if self.settings.os in ["Linux", "FreeBSD"] and self.options.with_thread:
            self.cpp_info.system_libs = ["pthread"]
