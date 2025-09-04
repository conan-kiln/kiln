import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class DlibConan(ConanFile):
    name = "dlib"
    description = "A toolkit for making real world machine learning and data analysis applications"
    topics = ("machine-learning", "deep-learning", "computer-vision")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://dlib.net"
    license = "BSL-1.0"
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_gif": [True, False],
        "with_jpeg": [True, False],
        "with_png": [True, False],
        "with_webp": [True, False],
        "with_sqlite3": [True, False],
        "with_sse2": [True, False, "auto"],
        "with_sse4": [True, False, "auto"],
        "with_avx": [True, False, "auto"],
        "with_openblas": [True, False],
        "with_cuda": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_gif": True,
        "with_jpeg": True,
        "with_png": True,
        "with_webp": True,
        "with_sqlite3": True,
        "with_sse2": "auto",
        "with_sse4": "auto",
        "with_avx": "auto",
        "with_openblas": True,
        "with_cuda": False,
    }

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def config_options(self):
        if self.settings.os == "Windows":
            self.options.rm_safe("fPIC")
        if self.settings.arch not in ["x86", "x86_64"]:
            self.options.rm_safe("with_sse2")
            self.options.rm_safe("with_sse4")
            self.options.rm_safe("with_avx")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if not self.options.with_cuda:
            del self.settings.cuda

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_gif:
            self.requires("giflib/[^5.2.1]")
        if self.options.with_jpeg:
            self.requires("libjpeg-meta/latest")
        if self.options.with_png:
            self.requires("libpng/[~1.6]")
        if self.options.with_webp:
            self.requires("libwebp/[^1.3.2]")
        if self.options.with_sqlite3:
            self.requires("sqlite3/[>=3.45.0 <4]")
        if self.options.with_openblas:
            self.requires("openblas/[>=0.3.28 <1]")

        if self.options.with_cuda:
            # Used in public dlib/cuda/cuda_utils.h
            self._utils.cuda_requires(self, "cudart", transitive_headers=True, transitive_libs=True)
            self._utils.cuda_requires(self, "cublas")
            self._utils.cuda_requires(self, "cusolver")
            self._utils.cuda_requires(self, "curand")
            self.requires("cudnn/[>=8 <10]")

    def validate(self):
        check_min_cppstd(self, 14 if Version(self.version) >= "19.24.2" else 11)
        if is_msvc(self) and self.options.shared:
            raise ConanInvalidConfiguration(f"{self.ref} does not support shared on Windows. See https://github.com/davisking/dlib/issues/1483.")
        if self.options.with_cuda:
            self._utils.validate_cuda_settings(self)

    def build_requirements(self):
        if self.options.with_cuda:
            self.tool_requires(f"nvcc/[~{self.settings.cuda.version}]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        save(self, "dlib/cmake_utils/test_for_cudnn/find_cudnn.txt",
             "find_package(cuDNN REQUIRED)\n"
             "set(cudnn cuDNN::cuDNN)\n"
             "set(cudnn_include ${cuDNN_INCLUDE_DIRS})\n")
        # sm_50 is no longer supported by newer CUDA versions
        replace_in_file(self, "dlib/cmake_utils/test_for_cuda/CMakeLists.txt", "-arch=sm_50;", "")
        replace_in_file(self, "dlib/cmake_utils/test_for_cudnn/CMakeLists.txt", "-arch=sm_50;", "")

    def _patch_sources(self):
        dlib_cmakelists = os.path.join(self.source_folder, "dlib", "CMakeLists.txt")
        # robust giflib injection
        replace_in_file(self, dlib_cmakelists, "${GIF_LIBRARY}", "GIF::GIF")
        # robust libjpeg injection
        for cmake_file in [
            dlib_cmakelists,
            os.path.join(self.source_folder, "dlib", "cmake_utils", "find_libjpeg.cmake"),
            os.path.join(self.source_folder, "dlib", "cmake_utils", "test_for_libjpeg", "CMakeLists.txt"),
        ]:
            replace_in_file(self, cmake_file, "${JPEG_LIBRARY}", "JPEG::JPEG")
        # robust libpng injection
        for cmake_file in [
            dlib_cmakelists,
            os.path.join(self.source_folder, "dlib", "cmake_utils", "find_libpng.cmake"),
            os.path.join(self.source_folder, "dlib", "cmake_utils", "test_for_libpng", "CMakeLists.txt"),
        ]:
            replace_in_file(self, cmake_file, "${PNG_LIBRARIES}", "PNG::PNG")
        # robust sqlite3 injection
        if self.options.with_sqlite3:
            replace_in_file(self, dlib_cmakelists, "find_library(sqlite sqlite3)", "find_package(SQLite3 REQUIRED)")
            replace_in_file(self, dlib_cmakelists, "find_path(sqlite_path sqlite3.h)", "")
            replace_in_file(self, dlib_cmakelists, "if (sqlite AND sqlite_path)", "if(1)")
            replace_in_file(self, dlib_cmakelists, "${sqlite}", "SQLite::SQLite3")
        # robust libwebp injection
        replace_in_file(self, dlib_cmakelists, "include(cmake_utils/find_libwebp.cmake)", "find_package(WebP REQUIRED)")
        replace_in_file(self, dlib_cmakelists, "if (WEBP_FOUND)", "if(1)")
        replace_in_file(self, dlib_cmakelists, "${WEBP_LIBRARY}", "WebP::webp")
        if self.options.with_png:
            replace_in_file(self, dlib_cmakelists, "include(cmake_utils/find_libpng.cmake)", "find_package(PNG REQUIRED)")
        if self.options.with_jpeg:
            replace_in_file(self, dlib_cmakelists, "include(cmake_utils/find_libjpeg.cmake)", "find_package(JPEG REQUIRED)")

    def generate(self):
        tc = CMakeToolchain(self)

        # With in-project builds dlib is always built as a static library,
        # we want to be able to build it as a shared library too
        tc.cache_variables["DLIB_IN_PROJECT_BUILD"] = False

        tc.cache_variables["DLIB_ISO_CPP_ONLY"] = False
        tc.cache_variables["DLIB_NO_GUI_SUPPORT"] = True
        # Configure external dependencies
        tc.cache_variables["DLIB_JPEG_SUPPORT"] = self.options.with_jpeg
        tc.cache_variables["DLIB_WEBP_SUPPORT"] = self.options.with_webp
        tc.cache_variables["DLIB_LINK_WITH_SQLITE3"] = self.options.with_sqlite3
        tc.cache_variables["DLIB_USE_BLAS"] = True    # FIXME: all the logic behind is not sufficiently under control
        tc.cache_variables["DLIB_USE_LAPACK"] = True  # FIXME: all the logic behind is not sufficiently under control
        tc.cache_variables["DLIB_PNG_SUPPORT"] = self.options.with_png
        tc.cache_variables["DLIB_GIF_SUPPORT"] = self.options.with_gif
        tc.cache_variables["DLIB_USE_MKL_FFT"] = False
        tc.cache_variables["DLIB_USE_CUDA"] = self.options.with_cuda
        tc.cache_variables["DLIB_USE_CUDA_COMPUTE_CAPABILITIES"] = ","  # Let NvccToolchain manage this
        # Skip the unnecessary test compiles that don't play well with Conan
        tc.cache_variables["cuda_test_compile_worked"] = True
        tc.cache_variables["cudnn_test_compile_worked"] = True

        # Configure SIMD options if possible
        if self.settings.arch in ["x86", "x86_64"]:
            if self.options.with_sse2 != "auto":
                tc.cache_variables["USE_SSE2_INSTRUCTIONS"] = self.options.with_sse2
            if self.options.with_sse4 != "auto":
                tc.cache_variables["USE_SSE4_INSTRUCTIONS"] = self.options.with_sse4
            if self.options.with_avx != "auto":
                tc.cache_variables["USE_AVX_INSTRUCTIONS"] = self.options.with_avx
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

        if self.options.with_cuda:
            nvcc_tc = self._utils.NvccToolchain(self)
            nvcc_tc.generate()

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure(build_script_folder=os.path.join(self.source_folder, "dlib"))
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        copy(self, "LICENSE.txt", src=os.path.join(self.source_folder, "dlib"), dst=os.path.join(self.package_folder, "licenses"), keep_path=False)
        for dir_to_remove in [
            os.path.join("lib", "cmake"),
            os.path.join("lib", "pkgconfig"),
            os.path.join("include", "dlib", "cmake_utils"),
            os.path.join("include", "dlib", "external", "pybind11", "tools")
        ]:
            rmdir(self, os.path.join(self.package_folder, dir_to_remove))
        rm(self, "*.txt", os.path.join(self.package_folder, "include", "dlib"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "dlib")
        self.cpp_info.set_property("cmake_target_name", "dlib::dlib")
        self.cpp_info.set_property("pkg_config_name", "dlib-1")
        # INFO: Unix systems use dlib as library name, but on Windows it includes settings, e.g dlib19.24.0_release_64bit_msvc1933.lib
        self.cpp_info.libs = collect_libs(self)
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["pthread"]
        elif self.settings.os == "Windows":
            self.cpp_info.system_libs = ["ws2_32", "winmm", "comctl32", "gdi32", "imm32"]
