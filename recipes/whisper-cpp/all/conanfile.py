import os

from conan import ConanFile
from conan.tools.apple import is_apple_os
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class WhisperCppConan(ConanFile):
    name = "whisper-cpp"
    description = "High-performance inference of OpenAI's Whisper automatic speech recognition (ASR) model"
    license = "MIT"
    homepage = "https://github.com/ggerganov/whisper.cpp"
    topics = ("whisper", "asr")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_openmp": [True, False],
        "with_cuda": [True, False],
        "with_openvino": [True, False],
        "with_coreml": [True, False],
        "coreml_allow_fallback": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_openmp": True,
        "with_cuda": True,
        "with_openvino": False,
        "with_coreml": False,
        "coreml_allow_fallback": False,
    }
    implements = ["auto_shared_fpic"]

    python_requires = "conan-cuda/latest"
    python_requires_extend = "conan-cuda.Cuda"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if not is_apple_os(self):
            del self.options.with_coreml

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.options["ggml"].with_openmp = self.options.with_openmp
        if self.options.with_cuda:
            self.options["ggml"].with_cuda = True
        else:
            del self.settings.cuda
        if not self.options.get_safe("with_coreml"):
            del self.options.coreml_allow_fallback
        else:
            self.options["ggml"].with_coreml = True
            self.options["ggml"].coreml_allow_fallback = self.options.coreml_allow_fallback

    def requirements(self):
        self.requires("ggml/[>=0.9 <1]", transitive_headers=True, transitive_libs=True)
        if self.options.with_cuda:
            self.cuda.requires("cudart")
            self.cuda.requires("cublas")
        if self.options.with_openvino:
            self.requires("openvino/[>=2024.5.0]")
        if self.options.with_openmp:
            self.requires("openmp/system")

    def build_requirements(self):
        if self.options.with_cuda:
            self.tool_requires(f"nvcc/[~{self.settings.cuda.version}]")
            self.tool_requires("cmake/[>=3.18]")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["WHISPER_BUILD_TESTS"] = False
        tc.variables["WHISPER_BUILD_EXAMPLES"] = False
        tc.variables["BUILD_SHARED_LIBS"] = self.options.shared
        tc.variables["WHISPER_USE_SYSTEM_GGML"] = True
        tc.variables["WHISPER_CUDA"] = self.options.with_cuda
        tc.variables["WHISPER_OPENVINO"] = self.options.with_openvino
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

        if self.options.with_cuda:
            tc = self.cuda.CudaToolchain()
            tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        copy(self, "*",
             os.path.join(self.source_folder, "models"),
             os.path.join(self.package_folder, "share", self.name, "models"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "whisper")
        self.cpp_info.set_property("cmake_target_name", "whisper")
        self.cpp_info.set_property("pkg_config_name", "whisper")
        self.cpp_info.libs = ["whisper"]
        self.cpp_info.resdirs = ["share"]
        if is_apple_os(self):
            if self.options.with_coreml:
                self.cpp_info.frameworks.append("CoreML")
        elif self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["dl", "m", "pthread"]
