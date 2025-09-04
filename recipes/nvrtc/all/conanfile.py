import os
from functools import cached_property

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class NvRtcConan(ConanFile):
    name = "nvrtc"
    description = "NVRTC: a CUDA C++ to PTX runtime compilation library"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-CUDA-Toolkit-EULA"
    homepage = "https://docs.nvidia.com/cuda/nvrtc/"
    topics = ("cuda", "ptx", "compiler")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "cmake_alias": [True, False],
        "use_stubs": [True, False],
    }
    default_options = {
        "shared": False,
        "cmake_alias": True,
        "use_stubs": False,
    }

    python_requires = "conan-cuda/latest"

    @cached_property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self, enable_private=True)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.use_stubs

    def configure(self):
        if not self.options.shared:
            self.options.rm_safe("use_stubs")

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        del self.info.settings.cuda.architectures
        self.info.settings.cuda.version = self.cuda.major
        self.info.settings.rm_safe("cmake_alias")
        self.info.settings.rm_safe("use_stubs")

    def requirements(self):
        self.cuda.requires("cudart", transitive_headers=True, transitive_libs=True)
        self.cuda.requires("nvptxcompiler")

    def validate(self):
        self.cuda.validate_package("cuda_nvrtc")

    def build(self):
        self.cuda.download_package("cuda_nvrtc")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        # Note: excluding nvrtc.alt and nvrtc-builtins.alt, since there is zero documentation and known uses of them online as of 12.9.
        if self.settings.os == "Linux":
            if self.options.shared:
                copy(self, "*.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"), excludes="*.alt.*")
                copy(self, "*.so*", os.path.join(self.source_folder, "lib", "stubs"), os.path.join(self.package_folder, "lib", "stubs"), excludes="*.alt.*")
            else:
                copy(self, "*_static.a", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"), excludes="*.alt.*")
        else:
            bin_dir = os.path.join(self.source_folder, "bin", "x64") if self.cuda.major >= 13 else os.path.join(self.source_folder, "bin")
            lib_dir = os.path.join(self.source_folder, "lib", "x64")
            if self.options.shared:
                copy(self, "*.dll", bin_dir, os.path.join(self.package_folder, "bin"), excludes="*.alt.*")
                copy(self, "nvrtc.lib", lib_dir, os.path.join(self.package_folder, "lib"), excludes="*.alt.*")
            else:
                copy(self, "*_static.lib", lib_dir, os.path.join(self.package_folder, "lib"), excludes="*.alt.*")

    def package_info(self):
        suffix = "" if self.options.shared else "_static"
        alias_suffix = "_static" if self.options.shared else ""
        self.cpp_info.components["nvrtc_"].set_property("pkg_config_name", f"nvrtc-{self.cuda.version}")
        self.cpp_info.components["nvrtc_"].set_property("component_version", str(self.cuda.version))
        self.cpp_info.components["nvrtc_"].set_property("cmake_target_name", f"CUDA::nvrtc{suffix}")
        if self.options.get_safe("cmake_alias"):
            self.cpp_info.components["nvrtc_"].set_property("cmake_target_aliases", [f"CUDA::nvrtc{alias_suffix}"])
        self.cpp_info.components["nvrtc_"].libs = [f"nvrtc{suffix}"]
        if self.options.get_safe("use_stubs"):
            self.cpp_info.components["nvrtc_"].libdirs = ["lib/stubs", "lib"]
        self.cpp_info.components["nvrtc_"].requires = ["cudart::cudart_", "nvptxcompiler::nvptxcompiler"]
        if self.settings.os == "Linux" and not self.options.shared:
            self.cpp_info.components["nvrtc_"].system_libs = ["rt", "pthread", "m", "dl", "gcc_s", "stdc++"]

        if self.settings.os == "Linux" or not self.options.shared:
            self.cpp_info.components["nvrtc_builtins"].set_property("cmake_target_name", f"CUDA::nvrtc_builtins{suffix}")
            if self.options.get_safe("cmake_alias"):
                self.cpp_info.components["nvrtc_builtins"].set_property("cmake_target_aliases", [f"CUDA::nvrtc_builtins{alias_suffix}"])
            self.cpp_info.components["nvrtc_builtins"].libs = [f"nvrtc-builtins{suffix}"]
            self.cpp_info.components["nvrtc_builtins"].requires = ["cudart::cudart_"]
            if self.settings.os == "Linux" and not self.options.shared:
                self.cpp_info.components["nvrtc_builtins"].system_libs = ["rt", "pthread", "m", "dl", "gcc_s", "stdc++"]
            self.cpp_info.components["nvrtc_"].requires.append("nvrtc_builtins")
