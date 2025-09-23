import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.build import check_min_cppstd, check_min_cstd, stdcpp_library
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc

required_conan_version = ">=2.1"


class GgmlConan(ConanFile):
    name = "ggml"
    description = "The GGML tensor library for machine learning"
    license = "MIT"
    homepage = "https://github.com/ggml-org/ggml"
    topics = ("machine-learning", "tensor", "neural-networks", "ai")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],

        "lto": [True, False],

        # Backends
        "cpu": [True, False],
        "with_blas": [True, False],
        "with_cuda": [True, False],
        "with_hip": [True, False],
        "with_metal": [True, False],
        "with_musa": [True, False],
        "with_opencl": [True, False],
        "with_sycl": [True, False],
        "with_vulkan": [True, False],
        "with_webgpu": [True, False],

        "with_kleidiai": [True, False],
        "with_llamafile": [True, False],
        "with_memkind": [True, False],
        "with_openmp": [True, False],
        "with_rpc": [True, False],

        # CPU
        "cpu_repack": [True, False],
        "sse42": [True, False],
        "avx": [True, False],
        "avx_vnni": [True, False],
        "avx2": [True, False],
        "bmi2": [True, False],
        "avx512": [True, False],
        "avx512_vbmi": [True, False],
        "avx512_vnni": [True, False],
        "avx512_bf16": [True, False],
        "fma": [True, False],
        "f16c": [True, False],
        "amx_tile": [True, False],
        "amx_int8": [True, False],
        "amx_bf16": [True, False],
        "lasx": [True, False],
        "lsx": [True, False],
        "rvv": [True, False],
        "rv_zfh": [True, False],
        "xtheadvector": [True, False],
        "vxe": [True, False],
        "nnpa": [True, False],

        # CUDA
        "cuda_force_mmq": [True, False],
        "cuda_force_cublas": [True, False],
        "cuda_f16": [True, False],
        "cuda_no_peer_copy": [True, False],
        "cuda_no_vmm": [True, False],
        "cuda_fa": [True, False],
        "cuda_fa_all_quants": [True, False],
        "cuda_graphs": [True, False],

        # HIP
        "hip_graphs": [True, False],
        "hip_no_vmm": [True, False],
        "hip_rocwmma_fattn": [True, False],
        "hip_force_rocwmma_fattn_gfx12": [True, False],
        "hip_mmq_mfma": [True, False],
        "hip_export_metrics": [True, False],

        # MUSA
        "musa_graphs": [True, False],
        "musa_mudnn_copy": [True, False],

        # Vulkan
        "vulkan_check_results": [True, False],
        "vulkan_shader_debug_info": [True, False],
        "vulkan_validate": [True, False],
        "vulkan_run_tests": [True, False],

        # Metal
        "metal_use_bf16": [True, False],
        "metal_ndebug": [True, False],
        "metal_shader_debug": [True, False],
        "metal_embed_library": [True, False],

        # SYCL
        "sycl_target": ["nvidia", "amd", "generic"],
        "sycl_f16": [True, False],
        "sycl_graph": [True, False],
        "sycl_dnn": [True, False],

        # OpenCL
        "opencl_profiling": [True, False],
        "opencl_embed_kernels": [True, False],
        "opencl_use_adreno_kernels": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,

        "lto": False,

        # Backends
        "cpu": True,
        "with_blas": False,
        "with_cuda": False,
        "with_hip": False,
        "with_metal": False,
        "with_musa": False,
        "with_opencl": False,
        "with_sycl": False,
        "with_vulkan": False,
        "with_webgpu": False,

        "with_kleidiai": False,
        "with_llamafile": False,
        "with_memkind": False,
        "with_openmp": True,
        "with_rpc": False,

        # CPU instruction defaults
        "cpu_repack": True,
        "sse42": True,
        "avx": True,
        "avx_vnni": False,
        "avx2": True,
        "bmi2": True,
        "avx512": False,
        "avx512_vbmi": False,
        "avx512_vnni": False,
        "avx512_bf16": False,
        "fma": True,
        "f16c": True,
        "amx_tile": False,
        "amx_int8": False,
        "amx_bf16": False,
        "lasx": True,
        "lsx": True,
        "rvv": True,
        "rv_zfh": False,
        "xtheadvector": False,
        "vxe": True,
        "nnpa": False,

        # CUDA defaults
        "cuda_force_mmq": False,
        "cuda_force_cublas": False,
        "cuda_f16": False,
        "cuda_no_peer_copy": False,
        "cuda_no_vmm": False,
        "cuda_fa": True,
        "cuda_fa_all_quants": False,
        "cuda_graphs": False,

        # HIP defaults
        "hip_graphs": False,
        "hip_no_vmm": True,
        "hip_rocwmma_fattn": False,
        "hip_force_rocwmma_fattn_gfx12": False,
        "hip_mmq_mfma": True,
        "hip_export_metrics": False,

        # MUSA defaults
        "musa_graphs": False,
        "musa_mudnn_copy": False,

        # Vulkan defaults
        "vulkan_check_results": False,
        "vulkan_shader_debug_info": False,
        "vulkan_validate": False,
        "vulkan_run_tests": False,

        # Metal defaults
        "metal_use_bf16": False,
        "metal_ndebug": False,
        "metal_shader_debug": False,
        "metal_embed_library": True,

        # SYCL defaults
        "sycl_target": "generic",
        "sycl_f16": False,
        "sycl_graph": True,
        "sycl_dnn": True,

        # OpenCL defaults
        "opencl_profiling": False,
        "opencl_embed_kernels": True,
        "opencl_use_adreno_kernels": True,
    }
    implements = ["auto_shared_fpic"]

    python_requires = "conan-cuda/latest"
    python_requires_extend = "conan-cuda.Cuda"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

        arch = str(self.settings.arch)
        if arch not in ["x86", "x86_64"]:
            del self.options.sse42
            del self.options.avx
            del self.options.avx_vnni
            del self.options.avx2
            del self.options.bmi2
            del self.options.avx512
            del self.options.avx512_vbmi
            del self.options.avx512_vnni
            del self.options.avx512_bf16
            del self.options.fma
            del self.options.f16c
            del self.options.amx_tile
            del self.options.amx_int8
            del self.options.amx_bf16
        if arch != "mips64":
            del self.options.lasx
            del self.options.lsx
        if not arch.startswith("riscv"):
            del self.options.rvv
            del self.options.rv_zfh
            del self.options.xtheadvector
        if arch != "s390x":
            del self.options.vxe
            del self.options.nnpa

        if is_msvc(self):
            self.options.rm_safe("fma")
            self.options.rm_safe("f16c")
            self.options.rm_safe("amx_tile")
            self.options.rm_safe("amx_int8")
            self.options.rm_safe("amx_bf16")

        if not is_apple_os(self):
            del self.options.with_metal

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

        if not self.options.cpu:
            self.options.rm_safe("with_kleidiai")
            self.options.rm_safe("with_memkind")
            self.options.rm_safe("cpu_repack")
            self.options.rm_safe("sse42")
            self.options.rm_safe("avx")
            self.options.rm_safe("avx_vnni")
            self.options.rm_safe("avx2")
            self.options.rm_safe("bmi2")
            self.options.rm_safe("avx512")
            self.options.rm_safe("avx512_vbmi")
            self.options.rm_safe("avx512_vnni")
            self.options.rm_safe("avx512_bf16")
            self.options.rm_safe("fma")
            self.options.rm_safe("f16c")
            self.options.rm_safe("amx_tile")
            self.options.rm_safe("amx_int8")
            self.options.rm_safe("amx_bf16")
            self.options.rm_safe("lasx")
            self.options.rm_safe("lsx")
            self.options.rm_safe("rvv")
            self.options.rm_safe("rv_zfh")
            self.options.rm_safe("xtheadvector")
            self.options.rm_safe("vxe")
            self.options.rm_safe("nnpa")

        if not self.options.with_cuda:
            del self.settings.cuda
            del self.options.cuda_force_mmq
            del self.options.cuda_force_cublas
            del self.options.cuda_f16
            del self.options.cuda_no_peer_copy
            del self.options.cuda_no_vmm
            del self.options.cuda_fa
            del self.options.cuda_fa_all_quants
            del self.options.cuda_graphs

        if not self.options.with_hip:
            del self.options.hip_graphs
            del self.options.hip_no_vmm
            del self.options.hip_rocwmma_fattn
            del self.options.hip_force_rocwmma_fattn_gfx12
            del self.options.hip_mmq_mfma
            del self.options.hip_export_metrics

        if not self.options.with_musa:
            del self.options.musa_graphs
            del self.options.musa_mudnn_copy

        if not self.options.with_vulkan:
            del self.options.vulkan_check_results
            del self.options.vulkan_shader_debug_info
            del self.options.vulkan_validate
            del self.options.vulkan_run_tests

        if not self.options.get_safe("with_metal"):
            del self.options.metal_use_bf16
            del self.options.metal_ndebug
            del self.options.metal_shader_debug
            del self.options.metal_embed_library

        if not self.options.with_sycl:
            del self.options.sycl_target
            del self.options.sycl_f16
            del self.options.sycl_graph
            del self.options.sycl_dnn
        else:
            if self.options.sycl_target == "nvidia":
                self.options["onemath"].cublas = True
            elif self.options.sycl_target == "amd":
                self.options["onemath"].rocblas = True
            else:
                self.options["onemath"].shared = True

        if not self.options.with_opencl:
            del self.options.opencl_profiling
            del self.options.opencl_embed_kernels
            del self.options.opencl_use_adreno_kernels

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_blas and not is_apple_os(self):
            self.requires("openblas/[>=0.3.20 <1]")
        if self.options.with_openmp:
            self.requires("openmp/system")
        if self.options.cpu:
            if self.options.with_kleidiai:
                self.requires("kleidiai/[^1]")
            if self.options.with_memkind:
                self.requires("memkind/[>=1.10 <2]")
        if self.options.with_vulkan:
            self.requires("vulkan-loader/[^1.3]")
        if self.options.with_opencl:
            self.requires("opencl-icd-loader/[*]")
        if self.options.with_cuda:
            self.cuda.requires("cudart")
            self.cuda.requires("cublas")
        if self.options.with_sycl:
            self.requires("onemath/[>=0.7 <1]")
        if self.options.with_hip:
            self.requires("hip/[^5]")
            self.requires("rocblas/[^2.45]")

    def validate(self):
        check_min_cppstd(self, 17)
        if self.settings.get_safe("compiler.cstd"):
            check_min_cstd(self, 11)

        if self.options.get_safe("with_memkind"):
            raise ConanInvalidConfiguration("with_memkind=True is not yet supported")
        if self.options.with_hip:
            raise ConanInvalidConfiguration("with_hip=True is not yet supported")
        if self.options.with_musa:
            raise ConanInvalidConfiguration("with_musa=True is not yet supported")
        if self.options.with_webgpu:
            raise ConanInvalidConfiguration("with_webgpu=True is not yet supported")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.14]")
        if self.options.with_cuda:
            self.tool_requires(f"nvcc/[~{self.settings.cuda.version}]")
        if self.options.with_vulkan:
            self.tool_requires("glslang/[^1]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        replace_in_file(self, "CMakeLists.txt", "set(CMAKE_CXX_STANDARD 17)", "")
        replace_in_file(self, "CMakeLists.txt", "set(CMAKE_C_STANDARD 11)", "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["GGML_BUILD_TESTS"] = False
        tc.cache_variables["GGML_BUILD_EXAMPLES"] = False
        tc.cache_variables["GGML_STATIC"] = not self.options.shared
        tc.cache_variables["GGML_NATIVE"] = False
        tc.cache_variables["GGML_LTO"] = self.options.lto
        tc.cache_variables["GGML_CCACHE"] = False
        tc.cache_variables["GGML_FATAL_WARNINGS"] = False

        # Backends
        tc.cache_variables["GGML_CPU"] = self.options.cpu
        tc.cache_variables["GGML_ACCELERATE"] = self.options.with_blas and is_apple_os(self)
        tc.cache_variables["GGML_BLAS"] = self.options.with_blas
        tc.cache_variables["GGML_BLAS_VENDOR"] = "Apple" if is_apple_os(self) else "OpenBLAS"
        tc.cache_variables["GGML_LLAMAFILE"] = self.options.with_llamafile
        tc.cache_variables["GGML_CUDA"] = self.options.with_cuda
        tc.cache_variables["GGML_MUSA"] = self.options.with_musa
        tc.cache_variables["GGML_HIP"] = self.options.with_hip
        tc.cache_variables["GGML_VULKAN"] = self.options.with_vulkan
        tc.cache_variables["GGML_WEBGPU"] = self.options.with_webgpu
        tc.cache_variables["GGML_METAL"] = self.options.get_safe("with_metal", False)
        tc.cache_variables["GGML_RPC"] = self.options.with_rpc
        tc.cache_variables["GGML_SYCL"] = self.options.with_sycl
        tc.cache_variables["GGML_OPENCL"] = self.options.with_opencl
        tc.cache_variables["GGML_OPENMP"] = self.options.with_openmp

        # CPU options
        if self.options.cpu:
            tc.cache_variables["GGML_CPU_KLEIDIAI"] = self.options.with_kleidiai
            tc.cache_variables["GGML_CPU_HBM"] = self.options.with_memkind
            tc.cache_variables["GGML_CPU_REPACK"] = self.options.cpu_repack
            tc.cache_variables["GGML_SSE42"] = self.options.get_safe("sse42", False)
            tc.cache_variables["GGML_AVX"] = self.options.get_safe("avx", False)
            tc.cache_variables["GGML_AVX_VNNI"] = self.options.get_safe("avx_vnni")
            tc.cache_variables["GGML_AVX2"] = self.options.get_safe("avx2", False)
            tc.cache_variables["GGML_BMI2"] = self.options.get_safe("bmi2", False)
            tc.cache_variables["GGML_AVX512"] = self.options.get_safe("avx512", False)
            tc.cache_variables["GGML_AVX512_VBMI"] = self.options.get_safe("avx512_vbmi", False)
            tc.cache_variables["GGML_AVX512_VNNI"] = self.options.get_safe("avx512_vnni", False)
            tc.cache_variables["GGML_AVX512_BF16"] = self.options.get_safe("avx512_bf16", False)
            tc.cache_variables["GGML_FMA"] = self.options.get_safe("fma", False)
            tc.cache_variables["GGML_F16C"] = self.options.get_safe("f16c", False)
            tc.cache_variables["GGML_AMX_TILE"] = self.options.get_safe("amx_tile", False)
            tc.cache_variables["GGML_AMX_INT8"] = self.options.get_safe("amx_int8", False)
            tc.cache_variables["GGML_AMX_BF16"] = self.options.get_safe("amx_bf16", False)
            tc.cache_variables["GGML_LASX"] = self.options.get_safe("lasx", False)
            tc.cache_variables["GGML_LSX"] = self.options.get_safe("lsx", False)
            tc.cache_variables["GGML_RVV"] = self.options.get_safe("rvv", False)
            tc.cache_variables["GGML_RV_ZFH"] = self.options.get_safe("rv_zfh", False)
            tc.cache_variables["GGML_XTHEADVECTOR"] = self.options.get_safe("xtheadvector", False)
            tc.cache_variables["GGML_VXE"] = self.options.get_safe("vxe", False)
            tc.cache_variables["GGML_NNPA"] = self.options.get_safe("nnpa", False)

        # CUDA options
        if self.options.with_cuda:
            tc.cache_variables["GGML_CUDA_FORCE_MMQ"] = self.options.cuda_force_mmq
            tc.cache_variables["GGML_CUDA_FORCE_CUBLAS"] = self.options.cuda_force_cublas
            tc.cache_variables["GGML_CUDA_F16"] = self.options.cuda_f16
            tc.cache_variables["GGML_CUDA_NO_PEER_COPY"] = self.options.cuda_no_peer_copy
            tc.cache_variables["GGML_CUDA_NO_VMM"] = self.options.cuda_no_vmm
            tc.cache_variables["GGML_CUDA_FA"] = self.options.cuda_fa
            tc.cache_variables["GGML_CUDA_FA_ALL_QUANTS"] = self.options.cuda_fa_all_quants
            tc.cache_variables["GGML_CUDA_GRAPHS"] = self.options.cuda_graphs

        # HIP options
        if self.options.with_hip:
            tc.cache_variables["GGML_HIP_GRAPHS"] = self.options.hip_graphs
            tc.cache_variables["GGML_HIP_NO_VMM"] = self.options.hip_no_vmm
            tc.cache_variables["GGML_HIP_ROCWMMA_FATTN"] = self.options.hip_rocwmma_fattn
            tc.cache_variables["GGML_HIP_FORCE_ROCWMMA_FATTN_GFX12"] = self.options.hip_force_rocwmma_fattn_gfx12
            tc.cache_variables["GGML_HIP_MMQ_MFMA"] = self.options.hip_mmq_mfma
            tc.cache_variables["GGML_HIP_EXPORT_METRICS"] = self.options.hip_export_metrics

        # MUSA options
        if self.options.with_musa:
            tc.cache_variables["GGML_MUSA_GRAPHS"] = self.options.musa_graphs
            tc.cache_variables["GGML_MUSA_MUDNN_COPY"] = self.options.musa_mudnn_copy

        # Vulkan options
        if self.options.with_vulkan:
            tc.cache_variables["GGML_VULKAN_CHECK_RESULTS"] = self.options.vulkan_check_results
            tc.cache_variables["GGML_VULKAN_SHADER_DEBUG_INFO"] = self.options.vulkan_shader_debug_info
            tc.cache_variables["GGML_VULKAN_VALIDATE"] = self.options.vulkan_validate
            tc.cache_variables["GGML_VULKAN_RUN_TESTS"] = self.options.vulkan_run_tests

        # Metal options
        if self.options.get_safe("with_metal", False):
            tc.cache_variables["GGML_METAL_USE_BF16"] = self.options.metal_use_bf16
            tc.cache_variables["GGML_METAL_NDEBUG"] = self.options.metal_ndebug
            tc.cache_variables["GGML_METAL_SHADER_DEBUG"] = self.options.metal_shader_debug
            tc.cache_variables["GGML_METAL_EMBED_LIBRARY"] = self.options.metal_embed_library

        # SYCL options
        if self.options.with_sycl:
            tc.cache_variables["SUPPORTS_SYCL"] = True
            tc.cache_variables["GGML_SYCL_TARGET"] = str(self.options.sycl_target).upper()
            tc.cache_variables["GGML_SYCL_F16"] = self.options.sycl_f16
            tc.cache_variables["GGML_SYCL_GRAPH"] = self.options.sycl_graph
            tc.cache_variables["GGML_SYCL_DNN"] = self.options.sycl_dnn

        # OpenCL options
        if self.options.with_opencl:
            tc.cache_variables["GGML_OPENCL_PROFILING"] = self.options.opencl_profiling
            tc.cache_variables["GGML_OPENCL_EMBED_KERNELS"] = self.options.opencl_embed_kernels
            tc.cache_variables["GGML_OPENCL_USE_ADRENO_KERNELS"] = self.options.opencl_use_adreno_kernels

        # Backend loading
        tc.cache_variables["GGML_BACKEND_DL"] = False

        tc.cache_variables["CMAKE_TRY_COMPILE_CONFIGURATION"] = str(self.settings.build_type)
        tc.cache_variables["GIT_EXE"] = "-NOTFOUND"
        tc.cache_variables["GGML_GIT_DIRTY"] = False

        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("vulkan-loader", "cmake_target_name", "Vulkan::Vulkan")
        deps.generate()

        if self.options.with_cuda:
            cuda_tc = self.cuda.CudaToolchain()
            cuda_tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "ggml")
        self.cpp_info.set_property("cmake_target_name", "ggml::ggml")
        self.cpp_info.set_property("cmake_additional_variables_prefixes", ["GGML"])
        self.cpp_info.set_property("pkg_config_name", "ggml")

        # Base library
        self.cpp_info.components["ggml-base"].set_property("cmake_target_name", "ggml::ggml-base")
        self.cpp_info.components["ggml-base"].libs = ["ggml-base"]
        if self.options.with_openmp:
            self.cpp_info.components["ggml-base"].requires.append("openmp::openmp")
        if not self.options.shared:
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.components["ggml-base"].system_libs = ["m", "pthread", "dl"]
            if stdcpp_library(self):
                self.cpp_info.components["ggml-base"].system_libs.append(stdcpp_library(self))

        self.cpp_info.components["ggml_"].libs = ["ggml"]
        self.cpp_info.components["ggml_"].requires = ["ggml-base"]

        # CPU backend
        if self.options.cpu:
            self.cpp_info.components["ggml-cpu"].set_property("cmake_target_name", "ggml::ggml-cpu")
            self.cpp_info.components["ggml-cpu"].libs = ["ggml-cpu"]
            self.cpp_info.components["ggml-cpu"].requires = ["ggml-base"]
            if self.options.with_kleidiai:
                self.cpp_info.components["ggml-cpu"].requires.append("kleidiai::kleidiai")
            if self.options.with_memkind:
                self.cpp_info.components["ggml-cpu"].requires.append("memkind::memkind")
            if self.options.with_blas and is_apple_os(self):
                self.cpp_info.components["ggml-cpu"].frameworks = ["Accelerate"]

        # Backend components
        if self.options.with_cuda:
            self.cpp_info.components["ggml-cuda"].set_property("cmake_target_name", "ggml::ggml-cuda")
            self.cpp_info.components["ggml-cuda"].libs = ["ggml-cuda"]
            self.cpp_info.components["ggml-cuda"].requires = ["ggml-base", "cudart::cudart_", "cublas::cublas_"]

        if self.options.with_vulkan:
            self.cpp_info.components["ggml-vulkan"].set_property("cmake_target_name", "ggml::ggml-vulkan")
            self.cpp_info.components["ggml-vulkan"].libs = ["ggml-vulkan"]
            self.cpp_info.components["ggml-vulkan"].requires = ["ggml-base", "vulkan-loader::vulkan-loader"]

        if self.options.with_opencl:
            self.cpp_info.components["ggml-opencl"].set_property("cmake_target_name", "ggml::ggml-opencl")
            self.cpp_info.components["ggml-opencl"].libs = ["ggml-opencl"]
            self.cpp_info.components["ggml-opencl"].requires = ["ggml-base", "opencl-icd-loader::opencl-icd-loader"]

        if self.options.with_hip:
            self.cpp_info.components["ggml-hip"].set_property("cmake_target_name", "ggml::ggml-hip")
            self.cpp_info.components["ggml-hip"].libs = ["ggml-hip"]
            self.cpp_info.components["ggml-hip"].requires = ["ggml-base", "hip::hip", "rocblas::rocblas"]

        if self.options.get_safe("with_metal", False):
            self.cpp_info.components["ggml-metal"].set_property("cmake_target_name", "ggml::ggml-metal")
            self.cpp_info.components["ggml-metal"].libs = ["ggml-metal"]
            self.cpp_info.components["ggml-metal"].requires = ["ggml-base"]
            if self.settings.os == "Macos":
                self.cpp_info.components["ggml-metal"].frameworks = ["Foundation", "Metal", "MetalKit"]

        if self.options.with_blas:
            self.cpp_info.components["ggml-blas"].set_property("cmake_target_name", "ggml::ggml-blas")
            self.cpp_info.components["ggml-blas"].libs = ["ggml-blas"]
            self.cpp_info.components["ggml-blas"].requires = ["ggml-base", "openblas::openblas"]
            self.cpp_info.components["ggml"].requires.append("ggml-blas")

        if self.options.with_sycl:
            self.cpp_info.components["ggml-sycl"].set_property("cmake_target_name", "ggml::ggml-sycl")
            self.cpp_info.components["ggml-sycl"].libs = ["ggml-sycl"]
            self.cpp_info.components["ggml-sycl"].requires = ["ggml-base"]
            if self.options.sycl_target == "nvidia":
                self.cpp_info.components["ggml-sycl"].requires.append("onemath::onemath_blas_cublas")
            elif self.options.sycl_target == "amd":
                self.cpp_info.components["ggml-sycl"].requires.append("onemath::onemath_blas_rocblas")
            else:
                self.cpp_info.components["ggml-sycl"].requires.append("onemath::onemath_dynamic")

        if self.options.with_musa:
            self.cpp_info.components["ggml-musa"].set_property("cmake_target_name", "ggml::ggml-musa")
            self.cpp_info.components["ggml-musa"].libs = ["ggml-musa"]
            self.cpp_info.components["ggml-musa"].requires = ["ggml-base"]
